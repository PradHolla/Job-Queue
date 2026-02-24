import { useState, useEffect } from 'react'

function App() {
  const [jobs, setJobs] = useState([])
  const [dlqCount, setDlqCount] = useState(0)

  // Fetch data from our FastAPI backend
  const fetchData = async () => {
    try {
      const jobsRes = await fetch('http://localhost:8000/api/jobs')
      const jobsData = await jobsRes.json()
      setJobs(jobsData.jobs)

      const dlqRes = await fetch('http://localhost:8000/api/dlq')
      const dlqData = await dlqRes.json()
      setDlqCount(dlqData.dlq_count)
    } catch (error) {
      console.error("Error fetching data", error)
    }
  }

  // Poll the API every 2 seconds to get real-time updates
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  // Helper function to color-code statuses
  const getStatusColor = (status) => {
    switch(status) {
      case 'QUEUED': return 'orange'
      case 'PROCESSING': return 'blue'
      case 'COMPLETED': return 'green'
      case 'FAILED': return 'red'
      default: return 'gray'
    }
  }

  return (
    <div style={{ fontFamily: 'Arial', padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🚀 Distributed Job Queue Dashboard</h1>
      
      <div style={{ padding: '1rem', backgroundColor: '#3657ba', borderRadius: '8px', marginBottom: '2rem' }}>
        <h3>☠️ Dead Letter Queue</h3>
        <p>Jobs trapped in DLQ: <strong>{dlqCount}</strong></p>
      </div>

      <h2>Recent Jobs</h2>
      <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ccc' }}>
            <th>Job ID</th>
            <th>Task Name</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map(job => (
            <tr key={job.id} style={{ borderBottom: '1px solid #eee', height: '40px' }}>
              <td style={{ fontSize: '0.8rem', color: '#555' }}>{job.id}</td>
              <td>{job.task_name}</td>
              <td style={{ color: getStatusColor(job.status), fontWeight: 'bold' }}>
                {job.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App