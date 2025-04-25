import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyD5O22E_X4sE3YCg6BA1XbT31qAuq1QknE",
  authDomain: "irrixa-9b8c1.firebaseapp.com",
  projectId: "irrixa-9b8c1",
  storageBucket: "irrixa-9b8c1.firebasestorage.app",
  messagingSenderId: "950522417024",
  appId: "1:950522417024:web:9125daa6721a6c4d207b65"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
