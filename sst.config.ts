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
    const stage = $app.stage;
    const region = "us-west-2";
    const srcPath = path.join($cli.paths.root, "src");
    const awsDlcImage = `763104351884.dkr.ecr.${region}.amazonaws.com/pytorch-inference:2.1.0-gpu-py310`;

    const modelBucket = new sst.aws.Bucket(`${appName}-models`, {
      public: false,
    });

    // Build model.tar.gz directly (SageMaker expects: model.pkl at root + code/ folder)
    const modelTarPath = path.join(srcPath, "model.tar.gz");
    execSync(
      `cd "${srcPath}" && tar -czf model.tar.gz tabpfn_model.pkl --transform='s|sagemaker/|code/|' sagemaker/inference.py sagemaker/requirements.txt`,
      { stdio: "pipe" }
    );

    const contentHash = crypto
      .createHash("md5")
      .update(new Uint8Array(fs.readFileSync(modelTarPath)))
      .digest("hex")
      .slice(0, 8);
    const modelS3Key = `models/tabpfn-model-${contentHash}.tar.gz`;

    // Upload model.tar.gz to S3
    const modelArtifact = new aws.s3.BucketObjectv2(
      `${appName}-model-artifact`,
      {
        bucket: modelBucket.name,
        key: modelS3Key,
        source: new pulumi.asset.FileAsset(modelTarPath),
        contentType: "application/gzip",
      }
    );

    // IAM role for SageMaker
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

    new aws.iam.RolePolicyAttachment(`${appName}-sagemaker-full`, {
      role: sagemakerRole.name,
      policyArn: "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    });

    // S3 read policy for model artifacts
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
        })
      ),
    });

    // ECR pull policy for AWS DLC images
    new aws.iam.RolePolicyAttachment(`${appName}-ecr-read`, {
      role: sagemakerRole.name,
      policyArn: "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    });

    new aws.iam.RolePolicyAttachment(`${appName}-cloudwatch`, {
      role: sagemakerRole.name,
      policyArn: "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    });

    // Model S3 URI
    const modelDataUrl = $interpolate`s3://${modelBucket.name}/${modelS3Key}`;

    // SageMaker Model using AWS pre-built container
    const sagemakerModel = new aws.sagemaker.Model(
      `${appName}-model`,
      {
        executionRoleArn: sagemakerRole.arn,
        primaryContainer: {
          image: awsDlcImage,
          modelDataUrl: modelDataUrl,
          environment: {
            SAGEMAKER_PROGRAM: "inference.py",
            SAGEMAKER_SUBMIT_DIRECTORY: "/opt/ml/model/code",
            SAGEMAKER_CONTAINER_LOG_LEVEL: "20",
          },
        },
      },
      { dependsOn: [modelArtifact] }
    );

    // SageMaker Endpoint Configuration
    const instanceType =
      stage === "production" ? "ml.g5.xlarge" : "ml.g4dn.xlarge";

    const endpointConfig = new aws.sagemaker.EndpointConfiguration(
      `${appName}-endpoint-config`,
      {
        productionVariants: [
          {
            variantName: "primary",
            modelName: sagemakerModel.name,
            initialInstanceCount: 1,
            instanceType: instanceType,
            initialVariantWeight: 1,
          },
        ],
      }
    );

    // SageMaker Endpoint
    const endpoint = new aws.sagemaker.Endpoint(`${appName}-endpoint`, {
      endpointConfigName: endpointConfig.name,
    });

    // Lambda function to invoke SageMaker endpoint
    const invokerLambda = new sst.aws.Function(`${appName}-invoker`, {
      handler: "src/lambda/invoker.handler",
      runtime: "nodejs20.x",
      timeout: "60 seconds",
      memory: "256 MB",
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
      containerImage: awsDlcImage,
      instanceType: instanceType,
      estimatedCost:
        instanceType === "ml.g4dn.xlarge" ? "~$0.73/hr" : "~$1.41/hr",
    };
  },
});
