import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import DeviceInventory from './pages/DeviceInventory'
import DeviceDetail from './pages/DeviceDetail'
import RiskHeatmap from './pages/RiskHeatmap'
import BenchmarkPage from './pages/BenchmarkPage'
import MigrationPlanner from './pages/MigrationPlanner'
import UploadAnalysis from './pages/UploadAnalysis'
import IoTSecurityLab from './pages/IoTSecurityLab'

export default function App() {
    return (
        <div className="min-h-screen bg-[var(--color-bg-primary)]">
            <Navbar />
            <main className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/devices" element={<DeviceInventory />} />
                    <Route path="/devices/:id" element={<DeviceDetail />} />
                    <Route path="/heatmap" element={<RiskHeatmap />} />
                    <Route path="/benchmarks" element={<BenchmarkPage />} />
                    <Route path="/migration" element={<MigrationPlanner />} />
                    <Route path="/upload" element={<UploadAnalysis />} />
                    <Route path="/iot-lab" element={<IoTSecurityLab />} />
                </Routes>
            </main>
        </div>
    )
}
