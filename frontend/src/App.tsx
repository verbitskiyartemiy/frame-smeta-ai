import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { DemoStoreProvider } from './ai/DemoStore'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import CreateProject from './pages/CreateProject'
import Contractors from './pages/Contractors'
import ContractorProfile from './pages/ContractorProfile'
import Estimates from './pages/Estimates'
import Messages from './pages/Messages'
import Documents from './pages/Documents'
import HomeHub from './pages/HomeHub'
import AIConsultant from './pages/AIConsultant'
import Community from './pages/Community'
import ForumTopic from './pages/ForumTopic'

export default function App() {
  return (
    <BrowserRouter>
      <DemoStoreProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/new" element={<CreateProject />} />
          <Route path="/project/:id" element={<ProjectDetail />} />
          <Route path="/contractors" element={<Contractors />} />
          <Route path="/contractors/:id" element={<ContractorProfile />} />
          <Route path="/estimates" element={<Estimates />} />
          <Route path="/messages" element={<Messages />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/home-hub" element={<HomeHub />} />
          <Route path="/community" element={<Community />} />
          <Route path="/community/topic/:id" element={<ForumTopic />} />
          <Route path="/ai" element={<AIConsultant />} />
        </Route>
      </Routes>
      </DemoStoreProvider>
    </BrowserRouter>
  )
}
