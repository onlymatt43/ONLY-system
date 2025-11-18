import express from 'express';
import { bypassAuthForVideos } from '../middleware/auth';

const router = express.Router();

// Apply relaxed auth for video streaming
router.use(bypassAuthForVideos);

router.get('/stream/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Set proper headers for video streaming
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Accept-Ranges', 'bytes');
    res.setHeader('Content-Type', 'video/mp4');
    
    // Stream video logic here
    // ...existing code...
  } catch (error) {
    console.error('Video streaming error:', error);
    res.status(500).json({ error: 'Failed to stream video' });
  }
});

export default router;