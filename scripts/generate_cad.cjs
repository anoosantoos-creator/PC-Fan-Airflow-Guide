const { mkdir, writeFile } = require("node:fs/promises");
const path = require("node:path");

global.__dirname = path.dirname(require.resolve("replicad-opencascadejs"));
global.require = require;

const openCascade = require("replicad-opencascadejs").default;
const replicad = require("replicad");

const OUTPUT_DIRECTORY = path.resolve(__dirname, "..", "cad_designs");
const REPRODUCIBLE_STEP_TIMESTAMP = "2000-01-01T00:00:00";
const STEP_TIMESTAMP_PATTERN =
  /(FILE_NAME\('Open CASCADE Shape Model',')\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(')/;

const COMMON = {
  frameSize: 120,
  openingRadius: 52.5,
  hubRadius: 20,
  screwSpacing: 105,
  screwRadius: 2.45,
  vaneInnerRadius: 18.5,
  vaneOuterRadius: 54,
};

const DESIGNS = [
  {
    file: "design_A_low_blockage",
    depth: 20,
    vaneCount: 6,
    vaneThickness: 1.5,
    vaneBias: 0,
  },
  {
    file: "design_B_angled_guide",
    depth: 25,
    vaneCount: 8,
    vaneThickness: 2,
    vaneBias: 14,
  },
  {
    file: "design_C_balanced_revision",
    depth: 22,
    vaneCount: 6,
    vaneThickness: 1.35,
    vaneBias: 9,
  },
];

function frame(depth) {
  const half = COMMON.frameSize / 2;
  let part = replicad
    .makeBox([0, -half, -half], [depth, half, half])
    .cut(
      replicad.makeCylinder(
        COMMON.openingRadius,
        depth + 2,
        [-1, 0, 0],
        [1, 0, 0]
      )
    );

  const offset = COMMON.screwSpacing / 2;
  for (const y of [-offset, offset]) {
    for (const z of [-offset, offset]) {
      part = part.cut(
        replicad.makeCylinder(
          COMMON.screwRadius,
          depth + 2,
          [-1, y, z],
          [1, 0, 0]
        )
      );
    }
  }
  return part;
}

function vane({ depth, vaneThickness, vaneBias }, azimuth) {
  const radialCenter =
    (COMMON.vaneInnerRadius + COMMON.vaneOuterRadius) / 2;
  return replicad
    .makeBox(
      [0, COMMON.vaneInnerRadius, -vaneThickness / 2],
      [depth, COMMON.vaneOuterRadius, vaneThickness / 2]
    )
    .rotate(vaneBias, [0, radialCenter, 0], [1, 0, 0])
    .rotate(azimuth, [0, 0, 0], [1, 0, 0]);
}

function guide(config) {
  let part = replicad.makeCylinder(
    COMMON.hubRadius,
    config.depth,
    [0, 0, 0],
    [1, 0, 0]
  );

  for (let index = 0; index < config.vaneCount; index += 1) {
    const nextVane = vane(config, (360 * index) / config.vaneCount);
    part = part.fuse(nextVane);
  }

  part = part.fuse(frame(config.depth));
  part = part.simplify();

  const solidCount = part._listTopo("solid").length;
  if (solidCount !== 1) {
    throw new Error(`${config.file} contains ${solidCount} disconnected solids`);
  }
  return part;
}

async function saveShape(shape, baseName) {
  const step = await shape.blobSTEP().arrayBuffer();
  const stl = await shape
    .blobSTL({ tolerance: 0.08, angularTolerance: 0.15, binary: true })
    .arrayBuffer();
  const stepText = Buffer.from(step).toString("utf8");
  if (!STEP_TIMESTAMP_PATTERN.test(stepText)) {
    throw new Error(`Could not normalize the STEP timestamp for ${baseName}`);
  }
  const reproducibleStep = stepText.replace(
    STEP_TIMESTAMP_PATTERN,
    `$1${REPRODUCIBLE_STEP_TIMESTAMP}$2`
  );
  await writeFile(
    path.join(OUTPUT_DIRECTORY, `${baseName}.step`),
    Buffer.from(reproducibleStep, "utf8")
  );
  await writeFile(path.join(OUTPUT_DIRECTORY, `${baseName}.stl`), Buffer.from(stl));
}

async function main() {
  const oc = await openCascade();
  replicad.setOC(oc);
  await mkdir(OUTPUT_DIRECTORY, { recursive: true });

  for (const config of DESIGNS) {
    const part = guide(config);
    await saveShape(part, config.file);
    console.log(`${config.file}: ${JSON.stringify(part.boundingBox.bounds)}`);
  }

  const referenceFrame = frame(25);
  const referenceHub = replicad.makeCylinder(
    20,
    25,
    [0, 0, 0],
    [1, 0, 0]
  );
  await saveShape(
    replicad.makeCompound([referenceFrame, referenceHub]),
    "fan_reference"
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
