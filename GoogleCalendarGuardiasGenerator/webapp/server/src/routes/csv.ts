import { Router } from "express";
import multer from "multer";
import { z } from "zod";
import { exportCsv, importCsv, saveCsvExport } from "../services/csv";

export const csvRouter = Router();

const upload = multer({ storage: multer.memoryStorage() });

csvRouter.post("/import", upload.single("file"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "Falta el fichero CSV (campo 'file')" });
  }
  const stats = importCsv(req.file.buffer, req.file.originalname);
  res.json(stats);
});

const exportSchema = z.object({
  asignaciones: z.array(
    z.object({
      fecha: z.string(),
      tecnico: z.string(),
      tipo: z.enum(["guardia", "media_guardia", "otro"]).optional(),
      titulo: z.string().optional()
    })
  )
});

csvRouter.post("/export", (req, res) => {
  const parsed = exportSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Payload inválido", details: parsed.error.flatten() });
  }

  const csvContent = exportCsv(parsed.data.asignaciones);
  saveCsvExport(csvContent);

  res.setHeader("Content-Type", "text/csv; charset=utf-8");
  res.setHeader("Content-Disposition", 'attachment; filename="guardias-support.csv"');
  res.send(csvContent);
});
