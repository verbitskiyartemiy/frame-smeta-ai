import { useEffect, useState, useCallback } from 'react'
import { projects as mockProjects, type Project } from '../data/mock'

const STORAGE_KEY = 'frame:projects'

function loadCustomProjects(): Project[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as Project[]
  } catch {
    return []
  }
}

function saveCustomProjects(list: Project[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

let listeners: Array<() => void> = []

function notify() {
  listeners.forEach((l) => l())
}

export function useProjects() {
  const [custom, setCustom] = useState<Project[]>(() => loadCustomProjects())

  useEffect(() => {
    const refresh = () => setCustom(loadCustomProjects())
    listeners.push(refresh)
    return () => {
      listeners = listeners.filter((l) => l !== refresh)
    }
  }, [])

  const addProject = useCallback((project: Project) => {
    const next = [...loadCustomProjects(), project]
    saveCustomProjects(next)
    notify()
  }, [])

  const removeProject = useCallback((id: string) => {
    const next = loadCustomProjects().filter((p) => p.id !== id)
    saveCustomProjects(next)
    notify()
  }, [])

  const allProjects = [...mockProjects, ...custom]

  return { projects: allProjects, addProject, removeProject, custom }
}

export function getProjectById(id: string): Project | undefined {
  const custom = loadCustomProjects()
  return [...mockProjects, ...custom].find((p) => p.id === id)
}
