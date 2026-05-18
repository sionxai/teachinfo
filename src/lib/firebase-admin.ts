import "server-only";

import { applicationDefault, cert, getApps, initializeApp, type App } from "firebase-admin/app";
import { getAuth, type Auth } from "firebase-admin/auth";
import { getFirestore, type Firestore } from "firebase-admin/firestore";
import { getStorage, type Storage } from "firebase-admin/storage";

let cachedApp: App | null | undefined;

function normalizePrivateKey(privateKey?: string) {
  return privateKey?.replace(/^"|"$/g, "").replace(/\\n/g, "\n");
}

export function getFirebaseAdminApp() {
  if (cachedApp !== undefined) return cachedApp;

  const projectId = process.env.FIREBASE_PROJECT_ID;
  const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
  const privateKey = normalizePrivateKey(process.env.FIREBASE_PRIVATE_KEY);
  const storageBucket = process.env.FIREBASE_STORAGE_BUCKET;

  try {
    if (getApps().length) {
      cachedApp = getApps()[0];
      return cachedApp;
    }

    if (projectId && clientEmail && privateKey) {
      cachedApp = initializeApp({
        credential: cert({ projectId, clientEmail, privateKey }),
        storageBucket,
      });
      return cachedApp;
    }

    if (projectId && process.env.GOOGLE_APPLICATION_CREDENTIALS) {
      cachedApp = initializeApp({
        credential: applicationDefault(),
        projectId,
        storageBucket,
      });
      return cachedApp;
    }

    cachedApp = null;
    return cachedApp;
  } catch {
    cachedApp = null;
    return cachedApp;
  }
}

export function getAdminDb(): Firestore | null {
  const app = getFirebaseAdminApp();
  return app ? getFirestore(app) : null;
}

export function getAdminAuth(): Auth | null {
  const app = getFirebaseAdminApp();
  return app ? getAuth(app) : null;
}

export function getAdminStorage(): Storage | null {
  const app = getFirebaseAdminApp();
  return app ? getStorage(app) : null;
}
