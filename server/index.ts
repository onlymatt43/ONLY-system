import express from 'express';
import cors from 'cors';
import axios from 'axios';

const app = express();
const PORT = process.env.PORT || 3000;

// Services Python existants
const SERVICES = {
  gateway: process.env.GATEWAY_URL || 'http://localhost:5055',
  curator: process.env.CURATOR_URL || 'http://localhost:5061',
  monetizer: process.env.MONETIZER_URL || 'http://localhost:5060',
  public: process.env.PUBLIC_URL || 'http://localhost:5062'
};

app.use(cors());
app.use(express.json());

// Proxy vers services Python
app.get('/api/videos', async (req, res) => {
  try {
    const response = await axios.get(`${SERVICES.curator}/videos`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch videos' });
  }
});

// Sentinel health check
app.get('/health', async (req, res) => {
  const health: Record<string, boolean> = {};
  
  for (const [name, url] of Object.entries(SERVICES)) {
    try {
      await axios.get(`${url}/health`, { timeout: 5000 });
      health[name] = true;
    } catch {
      health[name] = false;
    }
  }
  
  res.json({
    status: Object.values(health).every(v => v) ? 'healthy' : 'degraded',
    services: health
  });
});

app.listen(PORT, () => {
  console.log(`🚀 TypeScript proxy running on port ${PORT}`);
  console.log(`🛡️ Monitoring ${Object.keys(SERVICES).length} services`);
});