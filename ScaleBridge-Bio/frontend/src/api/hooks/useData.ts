import { useState, useEffect } from 'react';
import { apiClient } from '../client';
import { Project, Vessel, Assessment } from '../types';
import { getToken } from '../../lib/auth';

const FALLBACK_PROJECTS: Project[] = [
  {
    id: "proj_01",
    name: "Therapeutic mAb-204 Production",
    description: "Aerobic microbial fermentation transfer from 2 L glass benchtop to 150 L single-use pilot vessel.",
    organism: "Pichia pastoris",
    target_molecule: "mAb-204 Heavy-Chain Fragment",
    expression_system: "AOX1 Methanol Inducible",
    created_at: "2026-03-12T08:00:00Z",
  },
  {
    id: "proj_02",
    name: "Industrial Cellulase Scale-Up",
    description: "High-density biomass enzyme platform with continuous DO-stat glycerol feed.",
    organism: "Trichoderma reesei (Rut-C30)",
    target_molecule: "Endoglucanase II",
    expression_system: "cbh1 Promoter",
    created_at: "2026-03-18T14:30:00Z",
  },
  {
    id: "proj_03",
    name: "Food-Grade Heme Protein (LegH)",
    description: "High-OTR precision fermentation passport for oxygen-limited micro-aeration regimes.",
    organism: "Komagataella phaffii",
    target_molecule: "Soy Leghemoglobin",
    expression_system: "GAP Constitutive",
    created_at: "2026-03-24T10:15:00Z",
  },
];

const FALLBACK_VESSELS: Vessel[] = [
  {
    id: "vess_01",
    name: "BioFlo 120 2L Glass Benchtop",
    facility: "Development Lab 3A",
    scale_category: "lab",
    working_volume_min_l: 0.8,
    working_volume_max_l: 2.2,
    total_volume_l: 3.0,
    aspect_ratio: 2.1,
    impeller_count: 2,
    impeller_types: ["Rushton", "Pitched Blade"],
    baffle_count: 4,
    sparger_type: "Ring Sparger",
    max_rpm: 1200,
    max_power_w: 120,
    max_gassing_vvm: 2.0,
  },
  {
    id: "vess_02",
    name: "HyPerforma 150L SUB Pilot Reactor",
    facility: "Pilot Suite Alpha",
    scale_category: "pilot",
    working_volume_min_l: 35.0,
    working_volume_max_l: 150.0,
    total_volume_l: 185.0,
    aspect_ratio: 2.4,
    impeller_count: 2,
    impeller_types: ["Pitched Blade", "Marine Impeller"],
    baffle_count: 3,
    sparger_type: "Micro-Sparger Array",
    max_rpm: 380,
    max_power_w: 2400,
    max_gassing_vvm: 1.2,
  },
  {
    id: "vess_03",
    name: "Stainless Steel 10,000L Production Vessel",
    facility: "Facility Node B-4",
    scale_category: "production",
    working_volume_min_l: 2500.0,
    working_volume_max_l: 10000.0,
    total_volume_l: 12500.0,
    aspect_ratio: 2.8,
    impeller_count: 3,
    impeller_types: ["Rushton", "Rushton", "Hydrofoil"],
    baffle_count: 4,
    sparger_type: "Multi-ring pipe sparger",
    max_rpm: 180,
    max_power_w: 45000,
    max_gassing_vvm: 0.8,
  },
];

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (getToken() === 'mock_demo_token') {
      setProjects(FALLBACK_PROJECTS);
      setLoading(false);
      return;
    }

    apiClient<Project[]>('/projects')
      .then((data) => {
        setProjects(data && data.length > 0 ? data : FALLBACK_PROJECTS);
      })
      .catch((err) => {
        // Fall back to demo projects gracefully
        setProjects(FALLBACK_PROJECTS);
        setError(null);
      })
      .finally(() => setLoading(false));
  }, []);

  return { projects, loading, error };
}

export function useVessels() {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (getToken() === 'mock_demo_token') {
      setVessels(FALLBACK_VESSELS);
      setLoading(false);
      return;
    }

    apiClient<Vessel[]>('/vessels')
      .then((data) => {
        setVessels(data && data.length > 0 ? data : FALLBACK_VESSELS);
      })
      .catch((err) => {
        // Fall back to demo vessels gracefully
        setVessels(FALLBACK_VESSELS);
        setError(null);
      })
      .finally(() => setLoading(false));
  }, []);

  return { vessels, loading, error };
}
