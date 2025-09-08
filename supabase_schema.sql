-- Supabase Database Schema for R_SIM Rocket Simulation Platform
-- Run this in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create simulation_status table for real-time progress tracking
CREATE TABLE IF NOT EXISTS simulation_status (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    simulation_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'Initializing',
    progress FLOAT DEFAULT 0,
    simulation_time FLOAT,
    message TEXT,
    cell_count INTEGER,
    iteration_count INTEGER,
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create simulation_results table for storing final results
CREATE TABLE IF NOT EXISTS simulation_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    simulation_id TEXT NOT NULL UNIQUE,
    results JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create mesh_files table for storing mesh file metadata
CREATE TABLE IF NOT EXISTS mesh_files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_size BIGINT,
    file_type TEXT NOT NULL, -- 'mesh', 'stl', 'case'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create projects table for user project management
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id TEXT,
    project_name TEXT NOT NULL,
    rocket_config JSONB NOT NULL,
    simulation_config JSONB,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_simulation_status_simulation_id ON simulation_status(simulation_id);
CREATE INDEX IF NOT EXISTS idx_simulation_results_simulation_id ON simulation_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_mesh_files_simulation_id ON mesh_files(simulation_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_simulation_status_updated_at 
    BEFORE UPDATE ON simulation_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE simulation_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE mesh_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (you can make these more restrictive later)
CREATE POLICY "Allow public read access to simulation_status" ON simulation_status
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access to simulation_status" ON simulation_status
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update access to simulation_status" ON simulation_status
    FOR UPDATE USING (true);

CREATE POLICY "Allow public read access to simulation_results" ON simulation_results
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access to simulation_results" ON simulation_results
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access to mesh_files" ON mesh_files
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access to mesh_files" ON mesh_files
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access to projects" ON projects
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access to projects" ON projects
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update access to projects" ON projects
    FOR UPDATE USING (true);

-- Create storage bucket for mesh files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('mesh-files', 'mesh-files', true)
ON CONFLICT (id) DO NOTHING;

-- Create storage policies for mesh files
CREATE POLICY "Allow public read access to mesh files" ON storage.objects
    FOR SELECT USING (bucket_id = 'mesh-files');

CREATE POLICY "Allow public upload access to mesh files" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'mesh-files');

CREATE POLICY "Allow public update access to mesh files" ON storage.objects
    FOR UPDATE USING (bucket_id = 'mesh-files');

-- Insert some sample data for testing
INSERT INTO simulation_status (simulation_id, status, progress, message) 
VALUES ('test-sim-001', 'Initializing', 0, 'Test simulation created')
ON CONFLICT (simulation_id) DO NOTHING;

-- Create a view for easy simulation monitoring
CREATE OR REPLACE VIEW simulation_monitor AS
SELECT 
    ss.simulation_id,
    ss.status,
    ss.progress,
    ss.simulation_time,
    ss.message,
    ss.cell_count,
    ss.iteration_count,
    ss.results,
    ss.created_at,
    ss.updated_at,
    sr.results as final_results,
    sr.completed_at
FROM simulation_status ss
LEFT JOIN simulation_results sr ON ss.simulation_id = sr.simulation_id
ORDER BY ss.updated_at DESC;
