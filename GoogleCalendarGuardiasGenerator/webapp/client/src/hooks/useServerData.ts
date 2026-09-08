import { useQuery } from "@tanstack/react-query";
import {
  getTecnicos,
  getFestivos,
  getGuardias,
  getGuardiasStats,
  getGoogleStatus,
  getGptStatus
} from "../api/resources";

export const useTecnicos = () => useQuery({ queryKey: ["tecnicos"], queryFn: getTecnicos });

export const useFestivos = () => useQuery({ queryKey: ["festivos"], queryFn: getFestivos });

export const useGuardias = () => useQuery({ queryKey: ["guardias"], queryFn: () => getGuardias() });

export const useGuardiasStats = () =>
  useQuery({ queryKey: ["guardias-stats"], queryFn: getGuardiasStats });

export const useGoogleStatus = () =>
  useQuery({ queryKey: ["google-status"], queryFn: getGoogleStatus, refetchOnWindowFocus: true });

export const useGptStatus = () => useQuery({ queryKey: ["gpt-status"], queryFn: getGptStatus });
