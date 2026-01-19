import {
  SageMakerRuntimeClient,
  InvokeEndpointCommand,
} from "@aws-sdk/client-sagemaker-runtime";
import type { APIGatewayProxyHandlerV2 } from "aws-lambda";

const client = new SageMakerRuntimeClient({
  region: process.env.AWS_REGION,
});
const ENDPOINT_NAME = process.env.SAGEMAKER_ENDPOINT_NAME!;

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  const path = event.rawPath || event.requestContext?.http?.path;
  const method = event.requestContext?.http?.method;

  // Health check endpoint
  if (path === "/health" && method === "GET") {
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status: "healthy",
        endpoint: ENDPOINT_NAME,
        timestamp: new Date().toISOString(),
      }),
    };
  }

  // Prediction endpoint
  if (path === "/predict" && method === "POST") {
    try {
      const body = event.body
        ? event.isBase64Encoded
          ? Buffer.from(event.body, "base64").toString()
          : event.body
        : "{}";

      console.log("Request body - /predict endpoint:", body);

      const command = new InvokeEndpointCommand({
        EndpointName: ENDPOINT_NAME,
        ContentType: "application/json",
        Body: new TextEncoder().encode(body),
      });

      const response = await client.send(command);

      console.log("SageMaker response - /predict endpoint:", response);

      const result = new TextDecoder().decode(response.Body);

      return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: result,
      };
    } catch (error: any) {
      console.error("SageMaker invocation error:", error);

      return {
        statusCode: 500,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          error: "Prediction failed",
          message: error.message,
        }),
      };
    }
  }

  return {
    statusCode: 404,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ error: "Not found" }),
  };
};
