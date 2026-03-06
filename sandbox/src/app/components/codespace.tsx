"use client";

import React, { useState, useEffect } from "react";
import CodeEditor from "@monaco-editor/react";

export default function Codespace() {
    const templates: any = {
        cpp: `#include<bits/stdc++.h>\n\nusing namespace std;\n\nint main(){\n    // write you code here \n}\n`,
        python: `#python doesn't need a template mate`,
        java: `import java.util.*;\nimport java.lang.*;\nimport java.io.*;\n\nclass Main\n{\n    public static void main (String[] args) throws java.lang.Exception\n    {\n        // write your code here\n    }\n}`
    };

    const [language, Setlanguage] = useState("cpp");
    const [code, setcode] = useState(templates[language]);
    const [input, setInput] = useState("");
    const [output, setOutput] = useState("Nothing to show yet...write some code");

    const [complexity, setComplexity] = useState("");
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const RunCode = async () => {
        fetch("/api/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code,
                language,
                input
            })
        }).then((res) => res.json())
            .then((data) => {
                setOutput(data.output);
            }).catch((err) => {
                setOutput("Error while running the code");
            });
    }

    const analyzeComplexity = async () => {
        

        setIsAnalyzing(true);
        setComplexity("Analyzing...");

        try {
            const backendURL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
            const response = await fetch(`${backendURL}/predict`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ code: code, language: language })
            });

            if (!response.ok) {
                throw new Error("Network response was not ok");
            }

            const data = await response.json();
            setComplexity(data.complexity);
        } catch (error) {
            console.error("Failed to fetch prediction:", error);
            setComplexity("Connection Error");
        } finally {
            setIsAnalyzing(false);
        }
    };

    useEffect(() => {
        setcode(templates[language]);
        setComplexity("");
    }, [language]);

    return (
        <div className="bg-gray-700 min-h-screen">
            <div className="flex flex-row items-center justify-between p-4 bg-gray-800 border-b border-gray-600">
                <div className="flex flex-row items-center space-x-4">
                    <select
                        value={language}
                        onChange={(e) => Setlanguage(e.target.value)}
                        className="bg-[#161B22] p-2 rounded text-white border border-gray-600 focus:outline-none focus:border-blue-500 transition-colors cursor-pointer"
                    >
                        <option value="cpp">C++</option>
                        <option value="python">Python</option>
                        <option value="java">Java</option>
                    </select>

                    <button
                        onClick={analyzeComplexity}
                        disabled={isAnalyzing}
                        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold py-2 px-6 rounded shadow-lg transform transition hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center space-x-2"
                    >
                        <span>{isAnalyzing ? "Processing..." : "Analyze Complexity"}</span>
                    </button>
                </div>

                <div className="flex items-center space-x-3 bg-[#0D1117] border border-gray-600 px-6 py-2 rounded-lg shadow-inner min-w-[250px] h-[42px]">
                    <span className="text-gray-400 text-sm font-semibold tracking-wider uppercase">Complexity:</span>
                    <span className={`font-mono font-bold text-lg ${(complexity && (complexity.includes('Error') || complexity.includes('only')))
                            ? 'text-red-400'
                            : 'text-green-400 drop-shadow-[0_0_8px_rgba(74,222,128,0.5)]'
                        }`}>
                        {complexity || "--"}
                    </span>
                </div>
            </div>

            <div className="flex flex-row border-t border-gray-600">
                <CodeEditor
                    height="85vh"
                    width="50%"
                    theme="vs-dark"
                    language={language}
                    value={code}
                    onChange={(e) => setcode(e || "")}
                     options={{
    accessibilitySupport: "off"
  }}
                />

                <div className="bg-gray-950 flex flex-col w-[50%] h-[85vh] text-white border-l border-gray-600 min-w-0">
                    <button
                        onClick={RunCode}
                        className="bg-blue-600 hover:bg-blue-500 transition-colors w-24 h-10 m-3 font-bold cursor-pointer rounded"
                    >
                        Run
                    </button>

                    <textarea 
                        onChange={(e) => setInput(e.target.value)}
                        className="w-[calc(100%-1.5rem)] max-w-full mx-3 mb-3 h-40 bg-[#0D1117] text-gray-200 p-3 border border-gray-600 rounded focus:outline-none focus:border-blue-500 resize-none overflow-x-auto"
                        placeholder="Enter custom input here..."
                    />
                    <div className="bg-[#0D1117] m-3 mt-0 p-3 border border-gray-600 rounded flex-grow overflow-auto">
                        <pre className="text-gray-300 font-mono text-sm whitespace-pre-wrap break-words">{output}</pre>
                    </div>
                </div>
            </div>
        </div>
    )
}