import path from "node:path";
import dotenv from "dotenv";

// Resuelve siempre relativo a la raíz de webapp/, sin importar el cwd desde el que se lance
const ROOT_DIR = path.resolve(__dirname, "..", "..");
dotenv.config({ path: path.join(ROOT_DIR, ".env") });

const DATA_DIR = path.resolve(ROOT_DIR, process.env.DATA_DIR || "./server/data");

export const config = {
  port: Number(process.env.PORT) || 3001,
  dataDir: DATA_DIR,
  tecnicosFile: path.join(DATA_DIR, "tecnicos.txt"),
  festivosFile: path.join(DATA_DIR, "festivos.txt"),
  calendariosFile: path.join(DATA_DIR, "calendarios.json"),
  csvDir: path.join(DATA_DIR, "csv"),
  csvExportFile: path.join(DATA_DIR, "csv", "guardias-support.csv"),

  openaiApiKey: process.env.OPENAI_API_KEY || "",
  openaiModel: process.env.OPENAI_MODEL || "gpt-4o-mini",

  googleCredentialsFile: path.resolve(
    ROOT_DIR,
    process.env.GOOGLE_CREDENTIALS_FILE || "./server/data/google_credentials.json"
  ),
  googleTokenFile: path.resolve(
    ROOT_DIR,
    process.env.GOOGLE_TOKEN_FILE || "./server/data/google_token.json"
  ),
  googleConfigFile: path.resolve(
    ROOT_DIR,
    process.env.GOOGLE_CONFIG_FILE || "./server/data/google_config.json"
  ),
  googleOAuthRedirect:
    process.env.GOOGLE_OAUTH_REDIRECT || "http://localhost:3001/api/google/oauth/callback"
};

