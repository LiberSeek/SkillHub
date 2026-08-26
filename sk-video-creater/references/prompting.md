# Wan and HappyHorse Prompting

Use this guide only when drafting or improving prompts for `wan` or `happyhorse`. Keep the user's named subjects, actions, setting, style, dialogue, and constraints intact. If the user supplies finished prompt text, use it as written unless they ask for improvement.

## Choose the Prompt Shape

### Text-to-video

Build a coherent description in this order:

1. Subject and defining appearance
2. Scene, time, weather, and lighting
3. One primary action with direction and speed
4. Shot size, camera angle, and one camera movement
5. Composition, lens character, color, and visual medium
6. Sound, dialogue, or music only when the selected model supports audio

Prefer one visually legible event for short clips. A useful compact pattern is:

```text
[subject] in [scene] performs [specific motion]. [shot size and angle]; the camera [single movement]. [lighting, color, lens, and style]. [supported sound intent].
```

### Image-to-video

The reference image already defines the subject, scene, composition, and style. Do not spend most of the prompt redescribing it. Specify:

- what moves, including body part or object and direction;
- how it moves: slowly, gently, quickly, gradually, or forcefully;
- camera direction and speed, or `fixed camera, no camera movement`;
- which elements must remain stable;
- sound intent only when supported.

Use concrete motion such as `slowly raises her right hand while her coat moves gently in the wind`, not vague phrases such as `the person moves naturally`.

### Reference-based role-play

When using `--mode r2v`, map reference order to `character1`, `character2`, and so on. Keep the prompt action-oriented and identify interactions explicitly:

```text
character1 enters the tea house and sets a cup on the table. character2 turns toward character1 and smiles. The camera slowly tracks right; both characters keep consistent identity, clothing, and facial features.
```

Wan 3.0 accepts unified `reference_image` media; HappyHorse R2V accepts up to nine `reference_image` media items. Do not use `character1` labels unless the corresponding references are supplied.

### First+last-frame transitions and video edits

For Wan 3.0 `--mode kf2v`, describe only the transformation between the supplied frames: camera path, subject motion, and continuity. When a `--video` or `--audio` input is supplied, describe how the generated result should preserve, extend, edit, or synchronize with that source. Do not request generated audio for a mode documented as silent.

For `--mode videoedit`, describe the edit operation and what must remain unchanged: `replace the coat with the reference wardrobe, preserve the person's face, pose, timing, and background motion`. Wan 3.0 uses a `video` media item; HappyHorse video edit uses `happyhorse-1.0-video-edit`.

## Cinematic Controls

Select only controls that clarify the requested result. Avoid keyword piles.

| Dimension | Useful choices |
| --- | --- |
| Shot size | close-up, medium shot, wide shot, extreme long shot |
| Angle | eye level, low angle, high angle, over-the-shoulder, aerial |
| Camera | fixed, slow push-in, pull-back, tracking left/right, orbit, crane up |
| Lens | wide-angle, normal lens, telephoto, shallow depth of field |
| Composition | centered, symmetrical, balanced, subject on left/right third |
| Lighting | daylight, overcast, backlight, rim light, firelight, neon |
| Color | warm, cool, muted, low saturation, high contrast |
| Medium | live action, 3D animation, claymation, pixel art, felt stop-motion |

Keep physical and camera motion compatible. For a five-second clip, one subject action plus one camera move is usually more coherent than several competing actions.

## Timing and Multiple Shots

Use timestamped shots only when the selected model and gateway support multi-shot generation. Keep the total timing equal to the requested duration:

```text
Overall mood and narrative style.
Shot 1 [0-3s]: wide shot, action and camera direction.
Shot 2 [3-5s]: transition, closer shot, finishing action and sound.
```

When using a DashScope model that documents `shot_type: "multi"`, pass `shot_type: "multi"` and `prompt_extend: true` through `--extra-json`. Do not add these fields to Wan 3.0 or HappyHorse merely because the prompt contains multiple shots; confirm current model support first.

For precise timing or composition, keep prompt expansion disabled when the provider exposes that option. For a short exploratory prompt, prompt expansion can help, but it may change literal details.

## Audio and Dialogue

First confirm that the exact model/input mode outputs audio. HappyHorse 1.1 supports audio output, but availability and controls may differ by gateway. Do not promise audio based only on audio words in the prompt.

When supported, describe sound at its source:

- Dialogue: `[speaker] says "..." in a calm, low voice at a measured pace.`
- Sound effect: `rain strikes the metal awning with a soft, dense patter.`
- Music: `restrained ambient electronic music, tense but not overpowering.`

Keep dialogue short enough for the clip. If the selected mode is silent, omit sound instructions or plan audio post-processing separately.

## Stability and Negative Guidance

Prefer positive constraints in the prompt: `the face and clothing remain consistent`, `the background architecture stays stable`, `smooth continuous movement`. If the provider/model accepts a negative prompt, a restrained default is:

```text
low quality, blurry, distorted anatomy, watermark, frozen motion, jitter, flicker, inconsistent lighting, identity drift
```

Do not inject a negative prompt automatically when the model does not document the field. For image-to-video, prioritize identity, geometry, and background stability over generic quality terms.

## Final Check

Before submission, verify that the prompt and parameters agree on:

- duration and the amount of action;
- aspect ratio and composition;
- camera movement and subject movement;
- reference-image role and stability constraints;
- audio expectations and actual model support;
- single-shot versus timed multi-shot structure.

This guide adapts prompting concepts from the Apache-2.0 licensed `qianwen-video-generation` skill published by QianWen AI Platform, version 0.0.1.
