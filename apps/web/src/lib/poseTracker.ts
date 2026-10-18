import {
  FilesetResolver,
  PoseLandmarker,
  type NormalizedLandmark,
  type PoseLandmarker as PoseLandmarkerInstance,
} from '@mediapipe/tasks-vision'

const WASM_PATH = '/mediapipe/wasm'
const MODEL_PATH = '/models/pose_landmarker_lite.task'

let filesetPromise: ReturnType<typeof FilesetResolver.forVisionTasks> | null = null

function visionFileset() {
  if (!filesetPromise) {
    filesetPromise = FilesetResolver.forVisionTasks(WASM_PATH)
  }
  return filesetPromise
}

export async function createPoseLandmarker(): Promise<PoseLandmarkerInstance> {
  const fileset = await visionFileset()
  const options = {
    runningMode: 'VIDEO' as const,
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
  }
  try {
    return await PoseLandmarker.createFromOptions(fileset, {
      ...options,
      baseOptions: { modelAssetPath: MODEL_PATH, delegate: 'GPU' },
    })
  } catch {
    return PoseLandmarker.createFromOptions(fileset, {
      ...options,
      baseOptions: { modelAssetPath: MODEL_PATH, delegate: 'CPU' },
    })
  }
}

export type PosePoint = NormalizedLandmark
