# Google Speech API Cost Analysis for KMITL Senior Project

## Available Credits with KMITL .edu Email

### 1. Google Cloud New User Credits
- **$300 free credits** for 90 days
- No payment required during trial
- All Google Cloud services included

### 2. GitHub Student Developer Pack
- **$100 Google Cloud credits** (in addition to $300)
- Valid for 1 year
- Get at: https://education.github.com/pack
- Requires: KMITL .edu email

### 3. Google Cloud for Education
- Contact KMITL IT department
- May provide additional **$50-$100** credits
- Check if KMITL has institutional agreement

### **Total Available Credits: ~$400-$500**

---

## Cost Breakdown

### Usage Estimates (Your App)
**Assumptions:**
- Average conversation: 10 exchanges
- STT: 5 seconds per user input × 10 = 50 sec/conversation
- TTS: 250 characters per response × 10 = 2,500 chars/conversation

### Pricing (After Free Tier)
- **STT**: $0.006 per 15 seconds (Standard model)
- **TTS**: $4 per 1M characters (Standard voices)
- **TTS**: $16 per 1M characters (WaveNet/Neural2 - premium)

### Per Conversation Cost
| Component | Standard | Premium (WaveNet) |
|-----------|----------|-------------------|
| STT (50 sec) | $0.02 | $0.02 |
| TTS (2,500 chars) | $0.01 | $0.04 |
| **Total** | **$0.03** | **$0.06** |

---

## Monthly Cost Projections

### With Free Tier (Ongoing)
- **STT**: 60 minutes/month free = ~72 conversations
- **TTS**: 4M characters/month free = ~1,600 conversations

**If you have <50 active users/day ’ stays FREE indefinitely**

### Beyond Free Tier

| Daily Users | Conversations/Month | Standard Cost | Premium Cost |
|-------------|---------------------|---------------|--------------|
| 10 | 300 | $9 | $18 |
| 50 | 1,500 | $45 | $90 |
| 100 | 3,000 | $90 | $180 |
| 500 | 15,000 | $450 | $900 |

---

## Timeline with Student Credits

### Phase 1: New User Credits ($300)
- **Duration**: 90 days
- **Coverage**: ~10,000 conversations (Standard) or ~5,000 (Premium)
- **Supports**: Heavy development + testing + demo

### Phase 2: GitHub Student Pack ($100)
- **Duration**: 1 year after Phase 1
- **Coverage**: ~3,333 conversations (Standard)
- **Supports**: Continued development

### Phase 3: Free Tier (Ongoing)
- **Forever**: 60 min STT + 4M chars TTS monthly
- **Coverage**: ~1,600 conversations/month
- **Supports**: ~50 daily active users

### **Total Free Period: ~15 months before any real costs**

---

## Alternative Solutions Comparison

### Option 1: Current Setup (Whisper base + pyttsx3)
- **Cost**: $0 (100% free)
- **Quality**: PP (Robotic TTS, decent STT)
- **Issue**: Artificial voice feedback from users

### Option 2: Upgrade Whisper + Keep pyttsx3
- **Cost**: $0 (100% free)
- **Quality**: PPP (Better STT, still robotic TTS)
- **Change**: Better accuracy, voice still artificial

### Option 3: Whisper (large) + OpenAI TTS
- **Cost**: $0.00375/conversation = ~$11/month (100 users)
- **Quality**: PPPP (Natural TTS, great STT)
- **Benefits**: 70% cheaper than Google, very natural voices

### Option 4: Whisper (large) + ElevenLabs
- **Cost**: $5-$11/month flat rate
- **Quality**: PPPPP (Most natural TTS available)
- **Benefits**: Predictable monthly cost, best quality

### Option 5: Google STT + TTS (Standard)
- **Cost**: $0.03/conversation = ~$90/month (100 users)
- **Quality**: PPPP (Very natural, great accuracy)
- **Benefits**: Enterprise-grade, reliable, your $400-500 credits

### Option 6: Google STT + TTS (WaveNet)
- **Cost**: $0.06/conversation = ~$180/month (100 users)
- **Quality**: PPPPP (Extremely natural, human-like)
- **Benefits**: Best available quality, your $400-500 credits

---

## Recommendation for KMITL Senior Project

### For Development & Demo (Next 3-6 months)
**Use Google Cloud Speech API (WaveNet)**
-  You have $400-500 in credits (covers everything)
-  Best quality for project presentation
-  Addresses user feedback about artificial voice
-  No cost during development
-  Easy to implement and reliable

### For Long-term/Production (After graduation)
**Switch to Whisper large + OpenAI TTS**
-  Much lower ongoing costs ($11 vs $180/month)
-  Still very natural quality
-  Easy migration (similar API structure)

---

## Setup Steps for Google Cloud

1. **Activate Student Benefits**
   - Go to: https://cloud.google.com/free
   - Sign up with KMITL .edu email
   - Get $300 credits (no credit card needed during trial)

2. **Get GitHub Student Pack**
   - Go to: https://education.github.com/pack
   - Verify with KMITL .edu email
   - Redeem $100 Google Cloud credits

3. **Enable APIs**
   - Go to Google Cloud Console
   - Enable "Cloud Speech-to-Text API"
   - Enable "Cloud Text-to-Speech API"

4. **Create Service Account**
   - Create credentials (Service Account Key)
   - Download JSON key file
   - Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS`

5. **Install SDK**
   ```bash
   pip install google-cloud-speech google-cloud-texttospeech
   ```

---

## Cost Monitoring Tips

1. **Set up billing alerts**
   - Alert at $50, $100, $200
   - Track usage in Cloud Console

2. **Use Standard voices during development**
   - Switch to WaveNet only for demos/production

3. **Implement caching**
   - Cache common TTS responses
   - Reduce redundant API calls

4. **Monitor free tier usage**
   - Stay within limits when possible
   - Use credits only when exceeding free tier

---

## Final Verdict

**For your senior project with $400-500 credits:**

 **Use Google Cloud Speech API**
- Zero cost for your entire project timeline
- Solves the artificial voice issue
- Professional quality for presentation
- Easy to implement
- Reliable and well-documented

You'll likely **never pay anything** for this project given your credits and free tier.
