async function loadSamples() {
  const response = await fetch("data/samples.json");
  if (!response.ok) {
    throw new Error(`Failed to load samples: ${response.status}`);
  }
  return response.json();
}

function badge(text) {
  const element = document.createElement("span");
  element.className = "badge";
  element.textContent = text;
  return element;
}

function buildAudioBlock(template, label, model, src, scoresText = "") {
  const fragment = template.content.firstElementChild.cloneNode(true);
  fragment.querySelector("strong").textContent = label;
  fragment.querySelector("span").textContent = model;
  fragment.querySelector("audio").src = `assets/${src}`;
  const scores = fragment.querySelector(".audio-scores");
  scores.textContent = scoresText;
  scores.hidden = !scoresText;
  return fragment;
}

function renderSample(sample, sampleIndex, sampleTemplate, audioTemplate) {
  const card = sampleTemplate.content.firstElementChild.cloneNode(true);
  card.querySelector(".sample-tag").textContent = `sample ${sampleIndex + 1}`;
  card.querySelector(".prompt").textContent = sample.prompt;

  const excerpt =
    sample.feedback_excerpt ||
    sample.lyrics_excerpt ||
    "";
  const excerptLabel = card.querySelector(".excerpt-label");
  excerptLabel.textContent = sample.feedback_excerpt
    ? "Feedback"
    : sample.lyrics_excerpt
      ? "Lyrics"
      : "";
  excerptLabel.hidden = !excerpt;
  card.querySelector(".excerpt").textContent = excerpt;
  const sampleScoresLabel = card.querySelector(".sample-scores-label");
  const sampleScores = card.querySelector(".sample-scores");
  let sampleScoresText = "";

  const badges = card.querySelector(".badge-row");

  if (sample.scores) {
    if ("mq_a" in sample.scores && "mq_b" in sample.scores) {
      sampleScoresLabel.textContent = "Preference";
      sampleScoresText =
        `Musicality : ${sample.preferences.musicality === "model_a" ? "A" : "B"}\n` +
        `Alignment: ${sample.preferences.alignment === "model_a" ? "A" : "B"}`;
    } else {
      sampleScoresLabel.textContent = "Preference";
      sampleScoresText =
        `Musicality : ${sample.preferences.musicality === "model_a" ? "A" : "B"} ｜ Confidence: ${sample.scores.music_conf}\n` +
        `Alignment: ${sample.preferences.alignment === "model_a" ? "A" : "B"} ｜ confidence: ${sample.scores.align_conf}`;
    }
  }
  sampleScoresLabel.hidden = !sampleScoresText;
  sampleScores.textContent = sampleScoresText;
  sampleScores.hidden = !sampleScoresText;
  badges.hidden = !badges.childElementCount;

  const audioBlocks = card.querySelector(".audio-blocks");
  if (sample.assets.ref) {
    audioBlocks.append(
      buildAudioBlock(audioTemplate, "Reference", "reference audio", sample.assets.ref)
    );
  }

  if (sample.assets.a) {
    const audioAScores = sample.scores && "mq_a" in sample.scores
      ? `Music Quality: ${sample.scores.mq_a}  |  Instruction Following: ${sample.scores.if_a}`
      : "";
    audioBlocks.append(
      buildAudioBlock(
        audioTemplate,
        "Audio A",
        sample.models.a,
        sample.assets.a,
        audioAScores
      )
    );
  }

  if (sample.assets.b) {
    const audioBScores = sample.scores && "mq_b" in sample.scores
      ? `Music Quality: ${sample.scores.mq_b}  |  Instruction Following: ${sample.scores.if_b}`
      : "";
      audioBlocks.append(
      buildAudioBlock(audioTemplate, "Audio B", sample.models.b, sample.assets.b, audioBScores)
    );
  }

  return card;
}

function renderDataset(dataset, datasetTemplate, sampleTemplate, audioTemplate) {
  const section = datasetTemplate.content.firstElementChild.cloneNode(true);
  section.querySelector("h2").textContent = dataset.label;
  section.querySelector(".section-description").textContent = dataset.description;

  const grid = section.querySelector(".sample-grid");
  dataset.samples.forEach((sample, index) => {
    grid.append(renderSample(sample, index, sampleTemplate, audioTemplate));
  });
  return section;
}

async function main() {
  const container = document.querySelector("#content");
  const datasetTemplate = document.querySelector("#dataset-template");
  const sampleTemplate = document.querySelector("#sample-template");
  const audioTemplate = document.querySelector("#audio-template");

  try {
    const payload = await loadSamples();
    container.innerHTML = "";
    payload.datasets.forEach((dataset) => {
      container.append(
        renderDataset(dataset, datasetTemplate, sampleTemplate, audioTemplate)
      );
    });
  } catch (error) {
    container.innerHTML = `<p class="loading">${error.message}</p>`;
  }
}

main();
