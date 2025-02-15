import dotenv from "dotenv";
dotenv.config();
import http from "node:http";
import https from "node:https";
const patchRequest = originalRequest => function (options, callback) {
    if (options && options.headers) {
        if (options.headers["x-region"]) delete options.headers["x-region"];
        if (options.headers["x-ms-region"]) delete options.headers["x-ms-region"];
    }
    return originalRequest(options, callback);
};
http.request = patchRequest(http.request);
https.request = patchRequest(https.request);
import ModelClient, { isUnexpected } from "@azure-rest/ai-inference";
import { AzureKeyCredential } from "@azure/core-auth";
const token = process.env["GITHUB_TOKEN"];
export async function main() {
    const client = new ModelClient("https://models.github.ai/inference", new AzureKeyCredential(token));
    const response = await client.path("/chat/completions").post({
        body: {
            messages: [{ role: "user", content: "Can you explain the basics of machine learning?" }],
            model: "DeepSeek-R1",
            max_tokens: 2048
        }
    });
    if (isUnexpected(response)) throw response.body.error;
    console.log(response.body.choices[0].message.content);
}
main().catch(err => {
    console.error("The sample encountered an error:", err);
});
