import express from "express";
import cors from "cors";
import path from "node:path";
import fs from "node:fs";
import { config } from "./config";
import { tecnicosRouter } from "./routes/tecnicos";
import { festivosRouter } from "./routes/festivos";
import { guardiasRouter } from "./routes/guardias";
import { csvRouter } from "./routes/csv";
import { googleRouter } from "./routes/google";
import { gptRouter } from "./routes/gpt";

const app = express();

app.use(cors({ origin: [/^http:\/\/localhost:\d+$/], credentials: false }));
app.use(express.json({ limit: "2mb" }));

app.get("/api/health", (_req, res) => res.json({ ok: true }));

app.use("/api/tecnicos", tecnicosRouter);
app.use("/api/festivos", festivosRouter);
app.use("/api/guardias", guardiasRouter);
app.use("/api/csv", csvRouter);
app.use("/api/google", googleRouter);
app.use("/api/gpt", gptRouter);

// En producción, sirve el build estático del cliente (webapp/client/dist)
const clientDist = path.resolve(__dirname, "..", "..", "client", "dist");
if (fs.existsSync(clientDist)) {
  app.use(express.static(clientDist));
  app.get("/*splat", (req, res, next) => {
    if (req.path.startsWith("/api")) return next();
    res.sendFile(path.join(clientDist, "index.html"));
  });
}

// Manejador de errores centralizado
// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || "Error interno del servidor" });
});

app.listen(config.port, () => {
  console.log(`Guardias server escuchando en http://localhost:${config.port}`);
  console.log(`DATA_DIR = ${config.dataDir}`);
});
