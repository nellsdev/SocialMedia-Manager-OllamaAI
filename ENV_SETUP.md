# Environment Configuration Setup

Copy these values into your `backend/.env` file.

## Required Variables

### App
```
APP_NAME="Social Media Manager"
DEBUG=true
```

### Supabase (from Dashboard → Project Settings → API)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ... (anon public key)
SUPABASE_SERVICE_KEY=eyJ... (service_role secret key)
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

### Fernet Encryption (generate your own, back it up!)

Generate a fresh key locally — never commit or share it:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the output in your `.env`:
```
FERNET_SECRET_KEY=<your-generated-key>
```
**IMPORTANT**: If you lose this key, all encrypted Instagram tokens become permanently unreadable. Store the backup outside the repository (password manager).

### WhatsApp Webhook
```
WHATSAPP_WEBHOOK_SECRET=a-very-long-random-secret-string
```

### Instagram / Meta Graph API
```
INSTAGRAM_CLIENT_ID=your-meta-app-id
INSTAGRAM_CLIENT_SECRET=your-meta-app-secret
INSTAGRAM_REDIRECT_URI=http://localhost:3000/settings/integrations
```

### CORS
```
CORS_ORIGINS=["http://localhost:3000"]
```

### Scheduling
```
SCHEDULER_DB_URL=sqlite:///./scheduler.db
```

### LLM / Ollama
```
OLLAMA_BASE_URL=http://localhost:11434
```

### Rate Limiting
```
RATE_LIMIT_AGENTS_PER_MINUTE=10
RATE_LIMIT_AGENTS_BURST=3
```

### Agent Cache
```
AGENT_CACHE_TTL_SECONDS=300
REDIS_URL=                      # leave empty for in-memory
```

### Agent Memory
```
AGENT_MEMORY_BACKEND=supabase   # or "engram" for dev
```

### Production Safeguards
```
REQUIRE_HTTPS_WEBHOOKS=false
```
