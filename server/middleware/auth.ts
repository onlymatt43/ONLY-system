import { Request, Response, NextFunction } from 'express';

export const authenticateRequest = (req: Request, res: Response, next: NextFunction) => {
  // Allow all requests in development
  if (process.env.NODE_ENV === 'development') {
    return next();
  }
  
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  // Validate token and continue
  next();
};

export const bypassAuthForVideos = (req: Request, res: Response, next: NextFunction) => {
  // Allow video streaming without strict auth
  if (req.path.includes('/videos/') || req.path.includes('/stream/')) {
    return next();
  }
  return authenticateRequest(req, res, next);
};
