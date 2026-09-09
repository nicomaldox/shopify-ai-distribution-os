-- 002_video_render_jobs.sql
-- Table for tracking asynchronous video rendering jobs

CREATE TABLE IF NOT EXISTS video_render_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'ACCEPTED', -- 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    visual_hook TEXT,
    narration_text TEXT,
    video_url TEXT,
    local_path TEXT,
    error_message TEXT,
    callback_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_video_render_jobs_status ON video_render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_video_render_jobs_created_at ON video_render_jobs(created_at);
