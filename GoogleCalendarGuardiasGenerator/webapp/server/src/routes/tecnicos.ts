import { Router } from "express";
import { loadTecnicos } from "../services/tecnicos";

export const tecnicosRouter = Router();

tecnicosRouter.get("/", (_req, res) => {
  res.json(loadTecnicos());
});
