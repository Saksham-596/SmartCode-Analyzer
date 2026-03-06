// import { NextResponse } from "next/server";
// import {exec} from "child_process";
// import fs from "fs/promises";
// import path from "path";
// import crypto from "crypto";
// import util from "util";

// // the thing is that exec thing was before async and await , so we has to convert exec into promise using util
// const execPromise = util.promisify(exec);
// export async function POST(req: Request) {
//     try{
//         const { code, language, input } = await req.json();
//         console.log("Received:", { code, language, input });
//         // for mulitple clicking on run button , need to create a id for a specific runn
//         const runID = crypto.randomUUID();
//         const tempDir =  path.join(process.cwd(),"temp"); // current working directory 
//         await fs.mkdir(tempDir,{recursive:true}) // if directory is already it doesn't make or overwrite in that it simply use the current one and does not throw error 
//         const Codefilepath = path.join(tempDir,`${runID}.${language === "python" ? "py" : language === "java" ? "java" : "cpp"}`);
//         const Inputfilepath = path.join(tempDir,`${runID}.text`);
//         await fs.writeFile(Codefilepath,code);
//         await fs.writeFile(Inputfilepath,input || "");
//         let output ="";
//         try {
//             if (language === "cpp") {
//                 const executablePath = path.join(tempDir, `${runID}.out`);
//                 await execPromise(`g++ ${Codefilepath} -o ${executablePath}`);

//                 const { stdout, stderr } = await execPromise(
//                     `${executablePath} < ${Inputfilepath}`,
//                     { timeout: 2000 }
//                 );

//                 output = stderr ? `Verdict : Runtime Error:\n${stderr}` : stdout;
//             }

//             else if (language === "python") {
//                 const { stdout, stderr } = await execPromise(
//                     `python3 ${Codefilepath} < ${Inputfilepath}`,
//                     { timeout: 2000 }
//                 );

//                 output = stderr ? `Verdict : Runtime Error:\n${stderr}` : stdout;
//             }

//             else if (language === "java") {
//                 // Java requires file name to match class name
//                 const javaFilePath = path.join(tempDir, `Main.java`);
//                 await fs.rename(Codefilepath, javaFilePath);

//                 await execPromise(`javac ${javaFilePath}`);

//                 const { stdout, stderr } = await execPromise(
//                     `java -cp ${tempDir} Main < ${Inputfilepath}`,
//                     { timeout: 2000 }
//                 );

//                 output = stderr ? `Verdict : Runtime Error:\n${stderr}` : stdout;
//             }

//         } catch (error: any) {
//             if (error.killed) {
//                 output = "Verdict : Time Limit Exceeded";
//             } else {
//                 output = `Verdict : Compilation/Error:\n${error.stderr || error.message}`;
//             }
//         }

//         try {
//             await fs.unlink(Codefilepath).catch(() => {});
//             await fs.unlink(Inputfilepath).catch(() => {});
//         } catch (cleanupError) {
//             console.error("failed to clean up files:", cleanupError);
//         }

//         return NextResponse.json({ output });

//     }catch(error){
//         return NextResponse.json({output : "Internal Error while running the code"} , {status:500});
//     }

// }
// ****---- all this code was for running the code in backend and now i will make it run in the frontend using web worker and docker container in backend for that i will create a new api route for creating a container and then i will use that container to run the code in the frontend using web worker ----****

import {NextResponse} from "next/server";
import {exec} from "child_process";
import util from "util";
import fs from "fs/promises";
import path from "path";
import crypto from "crypto";

const execPromise = util.promisify(exec);

export async function POST(req: Request){
    try{
        const {code, language,input} = await req.json();
        const runID = crypto.randomUUID();
        const tempDir = path.join(process.cwd(),"temp");
        const runDir  = path.join(tempDir,runID);

        await fs.mkdir(runDir,{recursive:true});
        const inputfilepath = path.join(runDir,"input.txt");
        await fs.writeFile(inputfilepath,input || "");
        let output = "";
        try{
            if(language === "cpp"){
                const Codefilepath = path.join(runDir,"main.cpp");
                await fs.writeFile(Codefilepath,code);
                // compiling it 
                await execPromise(`docker run --rm -v ${runDir}:/app sandbox-engine g++ /app/main.cpp -o /app/main.out`);
                // running it 
                const {stdout,stderr} = await execPromise(
                    `docker run --rm -v ${runDir}:/app sandbox-engine sh -c "/app/main.out < /app/input.txt"`,
                    {timeout:3000}
                );
                output = stderr ? `Runtime Error :\n${stderr}` : stdout ;
            }else if(language === "python"){   
                const Codefilepath = path.join(runDir,"main.py");
                await fs.writeFile(Codefilepath,code);
                const {stdout,stderr} = await execPromise(
                    `docker run --rm -v ${runDir}:/app sandbox-engine sh -c "python3 /app/main.py < /app/input.txt"`,
                    {timeout:3000}
                );
                output = stderr ? `Runtime Error :\n${stderr}` : stdout ;   
            }else if(language === "java"){
                const Codefilepath = path.join(runDir,"Main.java");
                await fs.writeFile(Codefilepath,code);
                await execPromise(`docker run --rm -v ${runDir}:/app sandbox-engine javac /app/Main.java`);
                const {stdout,stderr} = await execPromise(
                    `docker run --rm -v ${runDir}:/app sandbox-engine sh -c "cd /app && java Main < input.txt"`,
                    {timeout:3000}
                );
                output = stderr ? `Runtime Error :\n${stderr}` : stdout ;   
             }
        }catch(error : any){
            if(error.killed){
                output = "Time Limit Exceeded (TLE)";
            }else{
                output = `compilation/runtime error :\n${error.stderr || error.message}`;
            }
        }finally{
            await fs.rm(runDir,{recursive:true,force:true}).catch(()=>{});
        }
        return NextResponse.json({output});

    }catch(error){
        console.error(error);
        return NextResponse.json(
            {output : "Internal Error while running the code"} , {status:500}
        );
    }
}