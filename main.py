import React, { useRef, useState, useEffect } from "react";
import "./App.css";

const BACKEND_URL = "https://poetry-meter-backend.onrender.com/analyze";
const rhymeColors = ["red", "green", "purple", "orange", "teal", "pink"];

function App() {
  const editorRef = useRef(null);
  const [timeoutId, setTimeoutId] = useState(null);
  const [meter, setMeter] = useState(null);

  const handleInput = () => {
    const rawText = editorRef.current.innerText;

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    const id = setTimeout(() => {
      fetchAnalysis(rawText);
    }, 500);

    setTimeoutId(id);
  };

  const fetchAnalysis = async (rawText) => {
    try {
      const res = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText })
      });

      const data = await res.json();
      if (data.meter) setMeter(data.meter);
      renderFormattedText(data.lines);
    } catch (err) {
      console.error("Error fetching stress data:", err);
    }
  };

  const getCaretCharacterOffsetWithin = (element) => {
    const sel = window.getSelection();
    let charCount = -1;
    if (sel.focusNode && element.contains(sel.focusNode)) {
      const range = sel.getRangeAt(0);
      const preCaretRange = range.cloneRange();
      preCaretRange.selectNodeContents(element);
      preCaretRange.setEnd(range.endContainer, range.endOffset);
      charCount = preCaretRange.toString().length;
    }
    return charCount;
  };

  const setCaretPosition = (element, offset) => {
    let charIndex = 0;
    const nodeStack = [element];
    let node, found = false;

    while (!found && (node = nodeStack.pop())) {
      if (node.nodeType === 3) {
        const nextCharIndex = charIndex + node.length;
        if (offset >= charIndex && offset <= nextCharIndex) {
          const range = document.createRange();
          const sel = window.getSelection();
          range.setStart(node, offset - charIndex);
          range.collapse(true);
          sel.removeAllRanges();
          sel.addRange(range);
          found = true;
        }
        charIndex = nextCharIndex;
      } else {
        let i = node.childNodes.length;
        while (i--) {
          nodeStack.push(node.childNodes[i]);
        }
      }
    }
  };

  const renderFormattedText = (lines) => {
    const editor = editorRef.current;
    const scrollPos = editor.scrollTop;
    const caretOffset = getCaretCharacterOffsetWithin(editor);

    const rhymeMap = {};
    let nextColorIdx = 0;

    editor.innerHTML = "";

    lines.forEach((line) => {
      const lineDiv = document.createElement("div");

      line.forEach((item) => {
        const wordSpan = document.createElement("span");
        wordSpan.style.whiteSpace = "pre";

        if (item.syllables && item.stress && item.stress !== "unknown") {
          for (let i = 0; i < item.syllables.length; i++) {
            const syllable = item.syllables[i];
            const syllSpan = document.createElement("span");
            syllSpan.textContent = syllable;
            syllSpan.style.backgroundColor = item.stress[i] === "1" ? "#cce5ff" : "#fff7a3";
            wordSpan.appendChild(syllSpan);
          }
        } else {
          wordSpan.textContent = item.word;
          wordSpan.style.color = "gray";
        }

        if (item.rhymeGroup !== undefined && item.rhymeGroup !== null) {
          if (!(item.rhymeGroup in rhymeMap)) {
            rhymeMap[item.rhymeGroup] = rhymeColors[nextColorIdx % rhymeColors.length];
            nextColorIdx++;
          }
          wordSpan.style.borderBottom = `2px solid ${rhymeMap[item.rhymeGroup]}`;
        }

        lineDiv.appendChild(wordSpan);
        lineDiv.appendChild(document.createTextNode(" "));
      });

      editor.appendChild(lineDiv);
    });

    editor.scrollTop = scrollPos;
    setCaretPosition(editor, caretOffset);
    editor.focus();
  };

  return (
    <div className="page">
      {meter && (
        <div className="meter-header">
          <strong>Detected Meter: </strong>
          <span className="meter-term" title="Iambic meter consists of unstressed-stressed syllable pairs (da-DUM).">
            {meter}
          </span>
        </div>
      )}
      <div
        className="editor"
        contentEditable
        onInput={handleInput}
        ref={editorRef}
        spellCheck="false"
        suppressContentEditableWarning
        style={{ whiteSpace: "pre-wrap", outline: "none" }}
      ></div>
    </div>
  );
}

export default App;
