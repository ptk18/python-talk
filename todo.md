- add thai to eng translation when in Thai lang mode 

## Thai lang mode
Thai speech -> transcribed Thai sentence -> translate to English -> pass it to current nlp model 

## Eng lang mode 
Eng speech -> transcribed Eng sentence -> pass it to current nlp model 

- Thai localization (nav texts, settings, and response voice [TTS] will be in Thai language maybe with Gemini TTS)

- gives paraphrased sentences to model to teach nlp model more intelligent (giving possible structures to says a cmd to the nlp model)

- remove others ways to say it button from the frontend (we will not suggest to user), we will just use it to teach the nlp model behind the scence 

- make the settings (models chocies work properly)

- TTS and STT model settings (customizable by user)