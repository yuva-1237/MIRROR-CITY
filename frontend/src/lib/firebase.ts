import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  User as FirebaseUser
} from "firebase/auth";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
export const firebaseConfig = {
  apiKey: "AIzaSyDK10t2cTlwxE78raeHIqTs4pDMSbk9Q7A",
  authDomain: "river-interface-457208-t7.firebaseapp.com",
  projectId: "river-interface-457208-t7",
  storageBucket: "river-interface-457208-t7.firebasestorage.app",
  messagingSenderId: "638632467892",
  appId: "1:638632467892:web:964f56d373a3c04328e6e1",
  measurementId: "G-83243GH7XZ"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Analytics if supported in this environment
export let analytics: ReturnType<typeof getAnalytics> | null = null;
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  }).catch(() => {
    // Analytics is optional and might be blocked by browser ad-blockers
  });
}

export {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged
};

export type { FirebaseUser };
