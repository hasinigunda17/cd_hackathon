
const samples = {

    sum: `let x = 5;
let total = 0;

while (x > 0) {
    total = total + x;
    x = x - 1;
}

if (total == 15) {
    print "Correct!";
} else {
    print "Try again";
}

print total;`,

    condition: `let marks = 82;

if (marks >= 40) {
    print "Pass";
} else {
    print "Fail";
}

print marks;`,

    math: `let a = 12;
let b = 4;

let answer = (a + b) * 2 - 5;

print answer;
print a / b;`

};


const source = document.getElementById("source");

const sampleSelect = document.getElementById("sampleSelect");

const runButton = document.getElementById("runButton");

const errorBox = document.getElementById("error");

const results = document.getElementById("results");


sampleSelect.addEventListener("change", () => {

    source.value = samples[sampleSelect.value];

});


function pretty(value) {

    return JSON.stringify(value, null, 2);

}


function formatTime(value) {

    if (value === null) {
        return "—";
    }

    return Number(value).toFixed(6);

}


runButton.addEventListener("click", async () => {

    errorBox.hidden = true;

    runButton.disabled = true;

    runButton.textContent = "Running...";

    try {

        const response = await fetch("/api/compare", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                source: source.value
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error || "Something went wrong"
            );

        }


        showResults(data);


    } catch (error) {

        errorBox.textContent = error.message;

        errorBox.hidden = false;


    } finally {

        runButton.disabled = false;

        runButton.textContent = "Run Comparison";

    }

});


function showResults(data) {

    results.hidden = false;


    const correctness = document.getElementById("correctness");

    correctness.textContent = data.correct
        ? "✓ Both outputs match"
        : "Outputs do not match";


    correctness.style.background = data.correct
        ? "#e5f7ed"
        : "#fff0f0";


    correctness.style.color = data.correct
        ? "#187346"
        : "#a12c2c";


    document.getElementById("interpreterTotal").textContent =
        formatTime(data.interpreter.total);


    document.getElementById("compilerTotal").textContent =
        formatTime(data.compiler.total);


    document.getElementById("instructionCount").textContent =
        data.compiler.instruction_count;


    const phases = [
        "Lexical analysis",
        "Parsing",
        "Translation",
        "Execution"
    ];


    document.getElementById("timingRows").innerHTML =

        phases.map(phase => `

            <tr>

                <td>${phase}</td>

                <td>
                    ${formatTime(data.interpreter.timings[phase])}
                </td>

                <td>
                    ${formatTime(data.compiler.timings[phase])}
                </td>

            </tr>

        `).join("");


    document.getElementById("interpreterOutput").textContent =
        data.interpreter.output.join("\n") || "(no output)";


    document.getElementById("compilerOutput").textContent =
        data.compiler.output.join("\n") || "(no output)";


    document.getElementById("interpreterVariables").textContent =
        pretty(data.interpreter.variables);


    document.getElementById("compilerVariables").textContent =
        pretty(data.compiler.variables);


    document.getElementById("bytecode").textContent =

        data.compiler.bytecode.map((item, index) =>

            `${String(index).padStart(3, "0")}  ${item[0]}${
                item[1] === null
                    ? ""
                    : "  " + JSON.stringify(item[1])
            }`

        ).join("\n");


    const difference =
        data.compiler.total - data.interpreter.total;


    let message = "Both paths produced the same result. ";


    if (Math.abs(difference) < 0.001) {

        message +=
            "The measured totals are extremely close. Timer overhead may dominate this small test.";

    } else if (difference > 0) {

        message +=
            `The compiler path took about ${difference.toFixed(6)} ms longer in this run.`;

    } else {

        message +=
            `The compiler + VM path was about ${Math.abs(difference).toFixed(6)} ms faster in this run.`;

    }


    message +=
        " Run several larger programs before drawing a general performance conclusion.";


    document.getElementById("explanation").textContent =
        message;


    results.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// Run the first sample automatically

runButton.click();
