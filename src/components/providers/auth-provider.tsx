"use client";

import {
  onAuthStateChanged,
  signOut as firebaseSignOut,
  type User as FirebaseUser,
} from "firebase/auth";
import { doc, getDoc, serverTimestamp, setDoc } from "firebase/firestore";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { auth, db } from "@/lib/firebase/client";
import type { User } from "@/types";

type AuthContextValue = {
  firebaseUser: FirebaseUser | null;
  profile: User | null;
  loading: boolean;
  isAdmin: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue>({
  firebaseUser: null,
  profile: null,
  loading: true,
  isAdmin: false,
  signOut: async () => {},
});

const defaultSettings = {
  email: true,
  push: false,
  keywords: [],
  regions: [],
  orgTypes: [],
};

export async function ensureUserProfile(user: FirebaseUser) {
  if (!db) return null;

  const ref = doc(db, "users", user.uid);
  const snapshot = await getDoc(ref);

  if (!snapshot.exists()) {
    const profile: User = {
      id: user.uid,
      email: user.email ?? "",
      displayName: user.displayName ?? user.email?.split("@")[0] ?? "사용자",
      profileImage: user.photoURL ?? "",
      bio: "",
      specialties: [],
      regions: [],
      role: "user",
      notificationSettings: defaultSettings,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    };
    await setDoc(ref, profile);
    return profile;
  }

  return { id: snapshot.id, ...snapshot.data() } as User;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }

    return onAuthStateChanged(auth, async (user) => {
      setFirebaseUser(user);
      setProfile(user ? await ensureUserProfile(user) : null);
      setLoading(false);
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser,
      profile,
      loading,
      isAdmin: profile?.role === "admin",
      signOut: async () => {
        if (auth) await firebaseSignOut(auth);
      },
    }),
    [firebaseUser, loading, profile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
