import Groq from "groq-sdk";

const apiKey = import.meta.env.GROQ_API_KEY || process.env.GROQ_API_KEY;

if (!apiKey) {
  console.error("GROQ_API_KEY is missing. Please add it to your .env file.");
}

export const groq = new Groq({
  apiKey: apiKey,
});
