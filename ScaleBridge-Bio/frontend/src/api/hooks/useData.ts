import { useState, useEffect } from 'react';
import { apiClient } from '../client';
import { Project, Vessel, Assessment } from '../types';

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient<Project[]>('/projects')
      .then(setProjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { projects, loading, error };
}

export function useVessels() {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient<Vessel[]>('/vessels')
      .then(setVessels)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { vessels, loading, error };
}
