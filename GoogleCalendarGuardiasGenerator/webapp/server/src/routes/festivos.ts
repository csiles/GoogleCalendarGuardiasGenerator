import { Router } from "express";
import { loadFestivos } from "../services/festivos";

export const festivosRouter = Router();

festivosRouter.get("/", (_req, res) => {
  res.json(loadFestivos());
});
