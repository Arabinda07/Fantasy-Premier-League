import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App.jsx'

// Design lab stays out of the main bundle; opt in with ?design_lab
const labModules = import.meta.glob('./__design_lab/page.jsx')
const hasLab = './__design_lab/page.jsx' in labModules
const DesignLabPage = hasLab ? lazy(labModules['./__design_lab/page.jsx']) : null
const isLab = hasLab && new URLSearchParams(window.location.search).has('design_lab')

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {isLab ? (
      <Suspense fallback={null}>
        <DesignLabPage />
      </Suspense>
    ) : (
      <App />
    )}
  </StrictMode>,
)
