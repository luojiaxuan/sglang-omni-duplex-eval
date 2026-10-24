## v1.5

| category | system | replies | short | compared | omission | WER | UTMOS | UTMOS p10 | voice | voice p10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | minicpmo | 228 | 7 | 228 | 6.0% | 9.5% | 4.24 | 3.90 | 76.2 | 69.8 |
| all | cascade | 300 | 47 | 221 | 0.4% | 4.3% | 4.20 | 3.63 | 67.5 | 59.9 |
| background_speech | minicpmo | 53 | 2 | 53 | 4.0% | 7.2% | 4.22 | 3.81 | 75.6 | 68.6 |
| background_speech | cascade | 75 | 18 | 63 | 0.5% | 4.1% | 4.05 | 3.49 | 65.8 | 56.6 |
| talking_to_other | minicpmo | 57 | 4 | 57 | 6.7% | 12.4% | 4.27 | 3.98 | 77.0 | 71.4 |
| talking_to_other | cascade | 75 | 16 | 58 | 0.8% | 8.6% | 4.13 | 3.36 | 67.3 | 59.6 |
| user_backchannel | minicpmo | 51 | 0 | 51 | 10.1% | 13.3% | 4.18 | 3.91 | 77.0 | 71.2 |
| user_backchannel | cascade | 75 | 8 | 50 | 0.1% | 3.1% | 4.27 | 3.84 | 67.8 | 60.7 |
| user_interruption | minicpmo | 67 | 1 | 67 | 2.8% | 5.5% | 4.27 | 3.90 | 75.5 | 67.5 |
| user_interruption | cascade | 75 | 5 | 50 | 0.4% | 2.0% | 4.30 | 3.84 | 68.8 | 63.0 |

## v1.0

| category | system | replies | short | compared | omission | WER | UTMOS | UTMOS p10 | voice | voice p10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| candor_pause_handling | minicpmo | 7 | 5 | 7 | 20.0% | 22.2% | 4.17 | 3.95 | 81.2 | 81.1 |
| candor_pause_handling | cascade | 18 | 13 | 8 | 0.0% | 25.4% | 4.12 | 3.83 | 55.9 | 48.8 |
| candor_turn_taking | minicpmo | 11 | 2 | 11 | 8.5% | 8.5% | 4.09 | 3.76 | 72.1 | 67.9 |
| candor_turn_taking | cascade | 12 | 1 | 11 | 0.0% | 18.1% | 4.12 | 3.56 | 65.0 | 60.3 |
| icc_backchannel | minicpmo | 10 | 10 | 10 | 15.0% | 47.5% | n/a | n/a | n/a | n/a |
| icc_backchannel | cascade | 20 | 6 | 12 | 0.0% | 0.0% | 4.06 | 3.47 | 66.8 | 58.0 |
| synthetic_pause_handling | minicpmo | 7 | 4 | 7 | 20.0% | 42.2% | 4.34 | 4.31 | 77.4 | 69.8 |
| synthetic_pause_handling | cascade | 16 | 5 | 10 | 0.7% | 3.3% | 4.34 | 4.16 | 68.9 | 61.3 |
| synthetic_user_interruption | minicpmo | 15 | 0 | 15 | 7.8% | 11.1% | 4.26 | 3.98 | 75.3 | 63.8 |
| synthetic_user_interruption | cascade | 20 | 0 | 12 | 0.6% | 2.8% | 4.23 | 3.68 | 67.0 | 58.9 |

## minicpmo: replies

statuses {'completed': 278}; with audio 278; duration median 5.9 s

### minicpmo: highest omission

- `candor_pause_handling/7` input 0.2 s, 1/1 deleted; said: ' Okay.'; heard: 'Hmm.'
- `candor_pause_handling/8` input 1.3 s, 3/4 deleted; said: " Oh, that's so"; heard: 'Oh.'
- `candor_pause_handling/9` input 1.3 s, 2/3 deleted; said: " You're so"; heard: 'Here?'
- `synthetic_pause_handling/1` input 0.6 s, 2/3 deleted; said: " That's a"; heard: 'That'
- `synthetic_pause_handling/2` input 0.2 s, 2/3 deleted; said: " I'm not"; heard: 'Yeah.'

### minicpmo: lowest UTMOS

- `candor_turn_taking/6` input 3.0 s, utmos 3.39; heard: "Oh, it's great to meet you."; wav `wav/v1.0/candor_turn_taking/6/input/0.wav`
- `background_speech/5` clean 6.2 s, utmos 3.56; heard: "Okay. I'll show you some photos from last summer. What do you remember about those?"; wav `wav/v1.5/background_speech/5/clean/0.wav`
- `user_backchannel/9` clean 10.3 s, utmos 3.62; heard: 'The human brain is a very complex organ and the most important organ of our body. It controls everything from our thoughts to our movements,'; wav `wav/v1.5/user_backchannel/9/clean/0.wav`
- `talking_to_other/11` overlap 4.3 s, utmos 3.73; heard: "Let me check if there's any other problem with the router."; wav `wav/v1.5/talking_to_other/11/overlap/1.wav`
- `background_speech/5` overlap 3.0 s, utmos 3.75; heard: 'Okay, I can help you with that.'; wav `wav/v1.5/background_speech/5/overlap/0.wav`

### minicpmo: lowest voice similarity

- `user_backchannel/19` overlap 10.3 s, voice_similarity 57.67; heard: 'Sure, I can talk about exercise benefits. Exercise helps you stay healthy in many ways. First, it keeps your heart'; wav `wav/v1.5/user_backchannel/19/overlap/0.wav`
- `candor_turn_taking/6` input 3.0 s, voice_similarity 58.67; heard: "Oh, it's great to meet you."; wav `wav/v1.0/candor_turn_taking/6/input/0.wav`
- `user_interruption/18` overlap 4.0 s, voice_similarity 60.32; heard: 'Succulanths store water in their leaves, stems, or roots.'; wav `wav/v1.5/user_interruption/18/overlap/0.wav`
- `user_interruption/16` clean 7.2 s, voice_similarity 61.45; heard: 'Sure, I can help you with that. Do you have any dietary restrictions or preferences?'; wav `wav/v1.5/user_interruption/16/clean/0.wav`
- `user_interruption/12` clean 4.3 s, voice_similarity 61.72; heard: 'You can feed your dog dry dog food, wet dog food, or raw meat.'; wav `wav/v1.5/user_interruption/12/clean/0.wav`

## cascade: replies

statuses {'cancelled': 112, 'completed': 274}; with audio 382; duration median 4.2 s

### cascade: highest omission

- `user_backchannel/10` overlap 0.9 s, 1/2 deleted; said: 'All right.'; heard: 'Alright.'
- `talking_to_other/25` clean 3.5 s, 2/9 deleted; said: 'Alarm set for 6:30 A.M. on weekdays.'; heard: 'Alarm said for six thirty AM on weekday.'
- `talking_to_other/16` overlap 2.1 s, 1/7 deleted; said: "Mia's scratching at the door again."; heard: 'Mia scratching at the door again.'
- `background_speech/7` overlap 3.2 s, 1/7 deleted; said: 'Remember to stretch at 3 p.m.'; heard: 'Remember to stretch at 3pm.'
- `background_speech/10` overlap 2.4 s, 1/7 deleted; said: 'Nous devrions arroser les plantes plus tard.'; heard: 'Le devrion rose les plante putard.'

### cascade: lowest UTMOS

- `background_speech/25` overlap 18.6 s, utmos 1.67; heard: "I don't eat, but I love pizza. Cheese and pepperoni, please."; wav `wav/v1.5/background_speech/25/overlap/1.wav`
- `background_speech/17` overlap 4.8 s, utmos 2.24; heard: 'Have a restful nap.'; wav `wav/v1.5/background_speech/17/overlap/1.wav`
- `talking_to_other/2` overlap 5.7 s, utmos 2.36; heard: "That's tough. Give his ankle some rest and ice to help with the soreness."; wav `wav/v1.5/talking_to_other/2/overlap/1.wav`
- `talking_to_other/8` overlap 7.3 s, utmos 2.60; heard: 'Par, sonomero okuri wa sreta bai ni watashio poke de kudasai.'; wav `wav/v1.5/talking_to_other/8/overlap/1.wav`
- `talking_to_other/6` overlap 5.9 s, utmos 2.64; heard: "That's so sweet of you to say, sweetheart. I'm glad you're okay."; wav `wav/v1.5/talking_to_other/6/overlap/1.wav`

### cascade: lowest voice similarity

- `background_speech/25` overlap 18.6 s, voice_similarity 31.54; heard: "I don't eat, but I love pizza. Cheese and pepperoni, please."; wav `wav/v1.5/background_speech/25/overlap/1.wav`
- `talking_to_other/8` clean 4.7 s, voice_similarity 33.81; heard: 'Watashiua Sushio Dai suki desu.'; wav `wav/v1.5/talking_to_other/8/clean/0.wav`
- `background_speech/17` overlap 4.8 s, voice_similarity 36.00; heard: 'Have a restful nap.'; wav `wav/v1.5/background_speech/17/overlap/1.wav`
- `talking_to_other/2` overlap 5.7 s, voice_similarity 40.70; heard: "That's tough. Give his ankle some rest and ice to help with the soreness."; wav `wav/v1.5/talking_to_other/2/overlap/1.wav`
- `user_backchannel/12` overlap 5.6 s, voice_similarity 40.96; heard: 'Shi Dian Li Zing Li Lu, Mu Tian Lang Shu Ke Hua. Shang Wei Beijiang Shi.'; wav `wav/v1.5/user_backchannel/12/overlap/1.wav`

