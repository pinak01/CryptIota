import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 120000,
    headers: { 'Content-Type': 'application/json' },
})

// Dashboard
export const fetchDashboardSummary = () => api.get('/dashboard/summary').then(r => r.data)
export const fetchHealth = () => api.get('/health').then(r => r.data)

// Devices
export const fetchDevices = (params = {}) => api.get('/devices', { params }).then(r => r.data)
export const fetchDevice = (id) => api.get(`/devices/${id}`).then(r => r.data)
export const addDevice = (data) => api.post('/devices', data).then(r => r.data)

// Classification
export const classifyDevice = (data) => api.post('/classify', data).then(r => r.data)

// Upload
export const uploadCSV = (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/csv', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
    }).then(r => r.data)
}

// Benchmarks
export const runBenchmark = (iterations = 50) =>
    api.get('/benchmark', { params: { iterations }, timeout: 300000 }).then(r => r.data)
export const fetchBenchmarkHistory = () => api.get('/benchmark/history').then(r => r.data)

// Migration
export const fetchMigrationRoadmap = () => api.get('/migration/roadmap').then(r => r.data)
export const fetchMigrationPlan = (id) => api.get(`/migration/plan/${id}`).then(r => r.data)
export const startDeviceMigration = (id, data) => api.post(`/devices/${id}/migrate`, data).then(r => r.data)
export const fetchMigrationStatus = (jobId) => api.get(`/migration/status/${jobId}`).then(r => r.data)

// Alerts
export const fetchAlerts = (params = {}) => api.get('/alerts', { params }).then(r => r.data)
export const acknowledgeAlert = (id) => api.post(`/alerts/${id}/acknowledge`).then(r => r.data)

// Reports
export const fetchDeviceReport = (id) => api.get(`/report/${id}`).then(r => r.data)

// Model
export const fetchModelInfo = () => api.get('/model/info').then(r => r.data)

// Crypto Demo
export const runCryptoDemo = (algo) => api.get(`/crypto/demo/${algo}`).then(r => r.data)

// IoT Security Lab
export const fetchIoTLabSummary = () => api.get('/iot-lab/summary').then(r => r.data)
export const fetchIoTLabDevices = () => api.get('/iot-lab/devices').then(r => r.data)
export const fetchIoTLabSessions = () => api.get('/iot-lab/sessions').then(r => r.data)
export const fetchIoTLabAttacks = (params = {}) => api.get('/iot-lab/attacks', { params }).then(r => r.data)
export const simulateAttack = (type) => api.post(`/iot-lab/simulate/${type}`).then(r => r.data)
export const registerIoTDevice = (data) => api.post('/iot-lab/devices/register', data).then(r => r.data)
export const initHandshake = (data) => api.post('/iot-lab/handshake/init', data).then(r => r.data)
export const completeHandshake = (data) => api.post('/iot-lab/handshake/complete', data).then(r => r.data)
export const sendTelemetry = (data) => api.post('/iot-lab/telemetry', data).then(r => r.data)

export default api
