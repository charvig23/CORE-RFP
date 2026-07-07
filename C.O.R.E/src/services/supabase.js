import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://zmjeumwgefzreqfjlilp.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InptamV1bXdnZWZ6cmVxZmpsaWxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI5OTMzMjAsImV4cCI6MjA5ODU2OTMyMH0.Gnwx1neMzpq7Si7Nf4YZQu2h9si88R2XmoOGZd5UVLY';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);