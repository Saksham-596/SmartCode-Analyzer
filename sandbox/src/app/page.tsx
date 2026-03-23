import Image from "next/image";

import styles from "./page.module.css";


import Navbar from "./components/Navbar";
import Codespace from "./components/codespace";

export default function Home() {
  return (
    <div className="bg-white h-screen w-full">
      <Navbar />
      <Codespace />
    </div>
  );
}
