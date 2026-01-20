/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app(input) {
    return {
      name: "sandbox-tabpfn-fraud-detection",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: input?.stage === "production",
      home: "aws",
      providers: {
        aws: {
          region: "us-west-2",
          profile: process.env.AWS_PROFILE || "asu-frog-sandbox",
        },
      },
    };
  },
  async run() {
    const aws = await import("@pulumi/aws");
    const pulumi = await import("@pulumi/pulumi");
    const fs = await import("fs");
    const path = await import("path");
    const crypto = await import("crypto");
    const { execSync } = await import("child_process");

    const appName = $app.name;
    const srcPath = path.join($cli.paths.root, "src");

    // Validate Docker image URI
    const dockerImageUri = process.env.DOCKER_IMAGE_URI;
    if (!dockerImageUri) {
      throw new Error(
        "DOCKER_IMAGE_URI not set. Run './build-and-push.sh' first and add the URI to .env file.",
      );
    }

    // Get image digest to force model updates when image changes
    let imageDigest = "unknown";
    try {
      const digestOutput = execSync(
        `aws ecr describe-images --repository-name tabpfn-fraud-detection --image-ids imageTag=latest --region us-west-2 --profile ${process.env.AWS_PROFILE || "asu-frog-sandbox"} --query 'imageDetails[0].imageDigest' --output text`,
        { stdio: "pipe" }
      ).toString().trim();
      // Extract only alphanumeric characters from digest
      imageDigest = digestOutput.replace(/[^a-zA-Z0-9]/g, "").substring(0, 12);
    } catch (error) {
      console.warn("Could not get image digest, using timestamp");
      imageDigest = Date.now().toString();
    }

    // Validate model file exists
    const modelPath = path.join(srcPath, "sagemaker", "tabpfn_classifier.tabpfn_fit");
    if (!fs.existsSync(modelPath)) {
      throw new Error(
        `Model file not found at ${modelPath}. Run 'cd src && python3 tabpfn_model_test.py' first.`,
      );
    }

    const modelBucket = new sst.aws.Bucket(`${appName}-models`, {
      public: false,
    });

    // Build model.tar.gz (SageMaker expects: tabpfn_classifier.tabpfn_fit at root)
    const modelTarPath = path.join(srcPath, "model.tar.gz");
    try {
      execSync(
        `cd "${srcPath}/sagemaker" && tar -czf ../model.tar.gz tabpfn_classifier.tabpfn_fit`,
        { stdio: "pipe" },
      );
    } catch (error) {
      throw new Error(`Failed to create model.tar.gz: ${error}`);
    }

    const contentHash = crypto
      .createHash("md5")
      .update(new Uint8Array(fs.readFileSync(modelTarPath)))
      .digest("hex")
      .slice(0, 8);
    const modelS3Key = `models/tabpfn-model-${contentHash}.tar.gz`;

    // Create combined version hash (image + model) to force updates when either changes
    const versionHash = crypto
      .createHash("md5")
      .update(imageDigest + contentHash)
      .digest("hex")
      .slice(0, 8);

    // Upload model.tar.gz to S3
    const modelArtifact = new aws.s3.BucketObjectv2(
      `${appName}-model-artifact`,
      {
        bucket: modelBucket.name,
        key: modelS3Key,
        source: new pulumi.asset.FileAsset(modelTarPath),
        contentType: "application/gzip",
      },
    );

    // IAM role for SageMaker with least-privilege policies
    const sagemakerRole = new aws.iam.Role(`${appName}-sagemaker-role`, {
      assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
          {
            Effect: "Allow",
            Principal: { Service: "sagemaker.amazonaws.com" },
            Action: "sts:AssumeRole",
          },
        ],
      }),
    });

    // S3 access for model artifacts
    new aws.iam.RolePolicy(`${appName}-s3-policy`, {
      role: sagemakerRole.name,
      policy: modelBucket.arn.apply((bucketArn: string) =>
        JSON.stringify({
          Version: "2012-10-17",
          Statement: [
            {
              Effect: "Allow",
              Action: ["s3:GetObject", "s3:ListBucket"],
              Resource: [bucketArn, `${bucketArn}/*`],
            },
          ],
        }),
      ),
    });

    // ECR access for Docker image
    new aws.iam.RolePolicy(`${appName}-ecr-policy`, {
      role: sagemakerRole.name,
      policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
          {
            Effect: "Allow",
            Action: [
              "ecr:GetAuthorizationToken",
              "ecr:BatchCheckLayerAvailability",
              "ecr:GetDownloadUrlForLayer",
              "ecr:BatchGetImage",
            ],
            Resource: "*",
          },
        ],
      }),
    });

    // CloudWatch Logs access (scoped to SageMaker)
    new aws.iam.RolePolicy(`${appName}-logs-policy`, {
      role: sagemakerRole.name,
      policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
          {
            Effect: "Allow",
            Action: [
              "logs:CreateLogGroup",
              "logs:CreateLogStream",
              "logs:PutLogEvents",
              "logs:DescribeLogStreams",
            ],
            Resource: "arn:aws:logs:*:*:log-group:/aws/sagemaker/*",
          },
        ],
      }),
    });

    // Model S3 URI
    const modelDataUrl = $interpolate`s3://${modelBucket.name}/${modelS3Key}`;

    // SageMaker Model using custom Docker container
    const sagemakerModel = new aws.sagemaker.Model(
      `${appName}-model`,
      {
        name: `${appName}-model-${versionHash}`, // Include version hash to force updates
        executionRoleArn: sagemakerRole.arn,
        primaryContainer: {
          image: dockerImageUri,
          modelDataUrl: modelDataUrl,
          environment: {
            SAGEMAKER_CONTAINER_LOG_LEVEL: "20",
            SAGEMAKER_MODEL_SERVER_TIMEOUT: "3600",
            SAGEMAKER_MODEL_SERVER_WORKERS: "1",
            OMP_NUM_THREADS: "4",
            MKL_NUM_THREADS: "4",
          },
        },
      },
      { dependsOn: [modelArtifact] },
    );

    // SageMaker Endpoint Configuration
    const instanceType =
      $app.stage === "production" ? "ml.g5.xlarge" : "ml.g4dn.xlarge";

    const endpointConfig = new aws.sagemaker.EndpointConfiguration(
      `${appName}-endpoint-config`,
      {
        name: `${appName}-endpoint-config-${versionHash}`, // Include version hash to force updates
        productionVariants: [
          {
            variantName: "primary",
            modelName: sagemakerModel.name,
            initialInstanceCount: 1,
            instanceType: instanceType,
            initialVariantWeight: 1,
          },
        ],
      },
    );

    // SageMaker Endpoint
    const endpoint = new aws.sagemaker.Endpoint(`${appName}-endpoint`, {
      endpointConfigName: endpointConfig.name,
    }, { 
      dependsOn: [endpointConfig],
      replaceOnChanges: ["endpointConfigName"] // Force recreation when config changes
    });

    // Lambda function to invoke SageMaker endpoint
    const invokerLambda = new sst.aws.Function(`${appName}-invoker`, {
      handler: "src/lambda/invoker.handler",
      runtime: "nodejs20.x",
      timeout: "900 seconds", // Increased for model loading + inference
      memory: "512 MB",
      environment: {
        SAGEMAKER_ENDPOINT_NAME: endpoint.name,
      },
      permissions: [
        {
          actions: ["sagemaker:InvokeEndpoint"],
          resources: [endpoint.arn],
        },
      ],
    });

    // API Gateway for external access
    const api = new sst.aws.ApiGatewayV2(`${appName}-api`);
    api.route("POST /predict", invokerLambda.arn);
    api.route("GET /health", invokerLambda.arn);

    return {
      endpointName: endpoint.name,
      endpointArn: endpoint.arn,
      apiUrl: api.url,
      modelDataUrl: modelDataUrl,
      dockerImage: dockerImageUri,
      instanceType: instanceType,
      estimatedCost:
        instanceType === "ml.g4dn.xlarge" ? "~$0.73/hr" : "~$1.41/hr",
    };
  },
});
