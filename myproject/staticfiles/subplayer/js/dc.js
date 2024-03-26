console.log('File loaded');
'use strict';

let dictionary = null; // This will hold the loaded dictionary
let config;

let savedTarget;


let selText;

let clientX;

let clientY;

let selStartDelta;

let selStartIncrement;

let popX = 0;

let popY = 0;

let timer;

let altView = 0;

let savedSearchResults = [];

let savedSelStartOffset = 0;

let savedSelEndList = [];

// regular expression for zero-width non-joiner U+200C &zwnj;
let zwnj = /\u200c/g;
class ZhongwenDictionary {
    constructor(wordDict, wordIndex, grammarKeywords, vocabKeywords) {
        this.wordDict = wordDict;
        this.wordIndex = wordIndex;
        this.grammarKeywords = grammarKeywords;
        this.vocabKeywords = vocabKeywords;
        this.cache = {};
    }

    static find(needle, haystack) {

        let beg = 0;
        let end = haystack.length - 1;

        while (beg < end) {
            let mi = Math.floor((beg + end) / 2);
            let i = haystack.lastIndexOf('\n', mi) + 1;

            let mis = haystack.substr(i, needle.length);
            if (needle < mis) {
                end = i - 1;
            } else if (needle > mis) {
                beg = haystack.indexOf('\n', mi + 1) + 1;
            } else {
                return haystack.substring(i, haystack.indexOf('\n', mi + 1));
            }
        }

        return null;
    }

    hasGrammarKeyword(keyword) {
        return this.grammarKeywords[keyword];
    }

    hasVocabKeyword(keyword) {
        return this.vocabKeywords[keyword];
    }

    wordSearch(word, max) {

        let entry = { data: [] };

        let dict = this.wordDict;
        let index = this.wordIndex;

        let maxTrim = max || 7;

        let count = 0;
        let maxLen = 0;

        WHILE:
            while (word.length > 0) {

                let ix = this.cache[word];
                if (!ix) {
                    ix = ZhongwenDictionary.find(word + ',', index);
                    if (!ix) {
                        this.cache[word] = [];
                        continue;
                    }
                    ix = ix.split(',');
                    this.cache[word] = ix;
                }

                for (let j = 1; j < ix.length; ++j) {
                    let offset = ix[j];

                    let dentry = dict.substring(offset, dict.indexOf('\n', offset));

                    if (count >= maxTrim) {
                        entry.more = 1;
                        break WHILE;
                    }

                    ++count;
                    if (maxLen === 0) {
                        maxLen = word.length;
                    }

                    entry.data.push([dentry, word]);
                }

                word = word.substr(0, word.length - 1);
            }

        if (entry.data.length === 0) {
            return null;
        }

        entry.matchLen = maxLen;
        return entry;
    }


    // Add other methods here as per your current code...
}

function search(text) {
    console.log("search");
    // Use `dictionary` instead of `dict`
    if (!dictionary) {
        // dictionary not loaded
        return;
    }

    let entry = dictionary.wordSearch(text);
    console.log(entry);
    if (entry) {
        for (let i = 0; i < entry.data.length; i++) {
            let word = entry.data[i][1];
            console.log("here "+word);
            if (dictionary.hasGrammarKeyword(word) && (entry.matchLen === word.length)) {
                // the final index should be the last one with the maximum length
                entry.grammar = { keyword: word, index: i };
                            console.log("here "+entry.grammar);

            }
            if (dictionary.hasVocabKeyword(word) && (entry.matchLen === word.length)) {
                // the final index should be the last one with the maximum length
                entry.vocab = { keyword: word, index: i };
                console.log("d "+entry.vocab);

            }
        }
    }

    return entry;
}
// Function to load dictionary data
async function loadDictData() {
    const basePath = DICT_BASE_PATH; // Use the global variable
    try {
        const wordDictPromise = fetch(`${basePath}cedict_ts.u8`).then(response => response.text());
        const wordIndexPromise = fetch(`${basePath}cedict.idx`).then(response => response.text());
        const grammarKeywordsPromise = fetch(`${basePath}grammarKeywordsMin.json`).then(response => response.json());
        const vocabKeywordsPromise = fetch(`${basePath}vocabularyKeywordsMin.json`).then(response => response.json());

        return await Promise.all([wordDictPromise, wordIndexPromise, grammarKeywordsPromise, vocabKeywordsPromise]);
    } catch (error) {
        console.error("Failed to load dictionary data:", error);
    }
}



// Function to initialize the dictionary
async function loadDictionary() {
    const [wordDict, wordIndex, grammarKeywords, vocabKeywords] = await loadDictData();
    dictionary = new ZhongwenDictionary(wordDict, wordIndex, grammarKeywords, vocabKeywords);
    return dictionary;
    console.log("Dictionary loaded successfully!");
}
// Execute the loadDictionary function when the document is fully loaded
document.addEventListener('DOMContentLoaded', async () => {
console.log("Dictionary loading...");
loadDictionary().then(() => {
  console.log("Dictionary loaded:", dictionary);
    // Assuming each entry is on a new line and format is "word - definition"
    const entries = dictionary.wordDict.split('\n');
    const firstEntry = entries[0];
    const [word, definition] = firstEntry.split(' / '); // Adjust split logic based on actual format

    console.log(`Word: ${word}, Definition: ${definition}`);
}).catch(error => {
  console.error("Error loading dictionary:", error);
});    // You can add other initializations here...
});

    



















let dictionaryIndex = {}; // Dictionary index object

// Example function to parse the IDX file content
// Assume `idxFileContent` is a string containing the content of the IDX file
function parseIdxFile(idxFileContent) {
    const lines = idxFileContent.split('\n');
    lines.forEach(line => {
        const [word, offset] = line.split(',');
        dictionaryIndex[word] = parseInt(offset, 10);
    });
}
// Function to fetch word data by byte offset from the server
async function fetchWordData(offset) {
    const response = await fetch('/path/to/your/dictionary.u8', {
        headers: {
            'Range': `bytes=${offset}-` // Fetch a specific byte range
        }
    });
    const text = await response.text(); // Assuming the response is text
    return text; // You might need to adjust this based on the actual format of your .u8 file
}
async function displayWordDataOnHover(word) {
    const offset = dictionaryIndex[word];
    if (typeof offset !== 'undefined') {
        const wordData = await fetchWordData(offset);
        // Show the word data in your popup
        console.log(wordData + " it is here poop" ); // Replace this with your actual popup display logic
    } else {
        console.log('Word not found in index.');
    }
}


// Elements for displaying the popup
let popup = null;
let savedRangeNode = null;
let savedRangeOffset = 0;

// Initialize the popup element
function initPopup() {
    popup = document.createElement('div');
    popup.id = 'dictionary-popup';
    popup.style.position = 'absolute';
    popup.style.display = 'none';
    popup.style.border = '1px solid black';
    popup.style.backgroundColor = 'white';
    popup.style.padding = '5px';
    popup.style.borderRadius = '5px';
    popup.style.zIndex = 10000; // Ensure it's on top of other elements
    document.body.appendChild(popup);
}

// Show the dictionary popup
function showPopup(html, x, y) {
    if (!popup) {
        initPopup();
    }
    popup.innerHTML = html;
    popup.style.left = `${x}px`;
    popup.style.top = `${y}px`;
    popup.style.display = 'block';
}

// Hide the dictionary popup
function hidePopup() {
    if (popup) {
        popup.style.display = 'none';
    }
}

function onMouseMove(mouseMove) {
    if (mouseMove.target.nodeName === 'TEXTAREA' || mouseMove.target.nodeName === 'INPUT'
        || mouseMove.target.nodeName === 'DIV') {

        let div = document.getElementById('zhongwenDiv');

    }

    if (clientX && clientY) {
        if (mouseMove.clientX === clientX && mouseMove.clientY === clientY) {
            return;
        }
    }
    clientX = mouseMove.clientX;
    clientY = mouseMove.clientY;

    let range;
    let rangeNode;
    let rangeOffset;

    // Handle Chrome and Firefox
    if (document.caretRangeFromPoint) {
        range = document.caretRangeFromPoint(mouseMove.clientX, mouseMove.clientY);
        if (range === null) {
            return;
        }
        rangeNode = range.startContainer;
        rangeOffset = range.startOffset;
    } else if (document.caretPositionFromPoint) {
        range = document.caretPositionFromPoint(mouseMove.clientX, mouseMove.clientY);
        if (range === null) {
            return;
        }
        rangeNode = range.offsetNode;
        rangeOffset = range.offset;
    }

    if (mouseMove.target === savedTarget) {
        if (rangeNode === savedRangeNode && rangeOffset === savedRangeOffset) {
            return;
        }
    }

    if (timer) {
        clearTimeout(timer);
        timer = null;
    }

    if (rangeNode.data && rangeOffset === rangeNode.data.length) {
        rangeNode = findNextTextNode(rangeNode.parentNode, rangeNode);
        rangeOffset = 0;
    }

    if (!rangeNode || rangeNode.parentNode !== mouseMove.target) {
        rangeNode = null;
        rangeOffset = -1;
    }

    savedTarget = mouseMove.target;
    savedRangeNode = rangeNode;
    savedRangeOffset = rangeOffset;

    selStartDelta = 0;
    selStartIncrement = 1;

    if (rangeNode && rangeNode.data && rangeOffset < rangeNode.data.length) {
        popX = mouseMove.clientX;
        popY = mouseMove.clientY;
        timer = setTimeout(() => triggerSearch(), 50);
        console.log("moved");

        return;
    }

    // Don't close just because we moved from a valid pop-up slightly over to a place with nothing.
    let dx = popX - mouseMove.clientX;
    let dy = popY - mouseMove.clientY;
    let distance = Math.sqrt(dx * dx + dy * dy);
    if (distance > 4) {
        clearHighlight();
        hidePopup();
    }
}

function triggerSearch() {
    let rangeNode = savedRangeNode;
    let selStartOffset = savedRangeOffset + selStartDelta;

    selStartIncrement = 1;

    if (!rangeNode) {
        clearHighlight();
        hidePopup();
        return 1;
    }

    if (selStartOffset < 0 || rangeNode.data.length <= selStartOffset) {
        clearHighlight();
        hidePopup();
        return 2;
    }

    let u = rangeNode.data.charCodeAt(selStartOffset);

    let isChineseCharacter = !isNaN(u) && (
        u === 0x25CB ||
        (0x3400 <= u && u <= 0x9FFF) ||
        (0xF900 <= u && u <= 0xFAFF) ||
        (0xFF21 <= u && u <= 0xFF3A) ||
        (0xFF41 <= u && u <= 0xFF5A) ||
        (0xD800 <= u && u <= 0xDFFF)
    );

    if (!isChineseCharacter) {

        clearHighlight();
        hidePopup();
        return 3;
    }

    let selEndList = [];
    let originalText = getText(rangeNode, selStartOffset, selEndList, 30 /*maxlength*/);

    // Workaround for Google Docs: remove zero-width non-joiner &zwnj;
    let text = originalText.replace(zwnj, '');

    savedSelStartOffset = selStartOffset;
    savedSelEndList = selEndList;

    searchResult=search(text);
    processSearchResult(searchResult);


    return 0;
}
function processSearchResult(result) {
    if (!result || result.data.length === 0) {
        alert('No definitions found.');
        return;
    }

    let alertMessage = "Definitions found:\n";
    result.data.forEach(([fullEntry, word], index) => {
        // Assuming the full entry format is "word [pinyin] /definition/"
        // You'll need to adjust the parsing based on your actual data format
        const definitionMatch = fullEntry.match(/\/(.+)\//);
        const definition = definitionMatch ? definitionMatch[1] : "No definition available";
        alertMessage += `${index + 1}. ${word}: ${definition}\n`;
    });

    alert(alertMessage);
}



// modifies selEndList as a side-effect
function getText(startNode, offset, selEndList, maxLength) {
    let text = '';
    let endIndex;

    if (startNode.nodeType !== Node.TEXT_NODE) {
        return '';
    }

    endIndex = Math.min(startNode.data.length, offset + maxLength);
    text += startNode.data.substring(offset, endIndex);
    selEndList.push({
        node: startNode,
        offset: endIndex
    });

    let nextNode = startNode;
    while ((text.length < maxLength) && ((nextNode = findNextTextNode(nextNode.parentNode, nextNode)) !== null)) {
        text += getTextFromSingleNode(nextNode, selEndList, maxLength - text.length);
    }

    return text;
}

// modifies selEndList as a side-effect
function getTextFromSingleNode(node, selEndList, maxLength) {
    let endIndex;

    if (node.nodeName === '#text') {
        endIndex = Math.min(maxLength, node.data.length);
        selEndList.push({
            node: node,
            offset: endIndex
        });
        return node.data.substring(0, endIndex);
    } else {
        return '';
    }
}

function showPopup(html, elem, x, y, looseWidth) {

    if (!x || !y) {
        x = y = 0;
    }

    let popup = document.getElementById('zhongwen-window');

    if (!popup) {
        popup = document.createElement('div');
        popup.setAttribute('id', 'zhongwen-window');
        document.documentElement.appendChild(popup);
    }

    popup.style.width = 'auto';
    popup.style.height = 'auto';
    popup.style.maxWidth = (looseWidth ? '' : '600px');
    popup.className = `background-${config.css} tonecolor-${config.toneColorScheme}`;

    $(popup).html(html);

    if (elem) {
        popup.style.top = '-1000px';
        popup.style.left = '0px';
        popup.style.display = '';

        let pW = popup.offsetWidth;
        let pH = popup.offsetHeight;

        if (pW <= 0) {
            pW = 200;
        }
        if (pH <= 0) {
            pH = 0;
            let j = 0;
            while ((j = html.indexOf('<br/>', j)) !== -1) {
                j += 5;
                pH += 22;
            }
            pH += 25;
        }

        if (altView === 1) {
            x = window.scrollX;
            y = window.scrollY;
        } else if (altView === 2) {
            x = (window.innerWidth - (pW + 20)) + window.scrollX;
            y = (window.innerHeight - (pH + 20)) + window.scrollY;
        } else if (elem instanceof window.HTMLOptionElement) {

            x = 0;
            y = 0;

            let p = elem;
            while (p) {
                x += p.offsetLeft;
                y += p.offsetTop;
                p = p.offsetParent;
            }

            if (elem.offsetTop > elem.parentNode.clientHeight) {
                y -= elem.offsetTop;
            }

            if (x + popup.offsetWidth > window.innerWidth) {
                // too much to the right, go left
                x -= popup.offsetWidth + 5;
                if (x < 0) {
                    x = 0;
                }
            } else {
                // use SELECT's width
                x += elem.parentNode.offsetWidth + 5;
            }
        } else {
            // go left if necessary
            if (x + pW > window.innerWidth - 20) {
                x = (window.innerWidth - pW) - 20;
                if (x < 0) {
                    x = 0;
                }
            }

            // below the mouse
            let v = 25;

            // go up if necessary
            if (y + v + pH > window.innerHeight) {
                let t = y - pH - 30;
                if (t >= 0) {
                    y = t;
                }
            } else  {
                y += v;
            }

            x += window.scrollX;
            y += window.scrollY;
        }
    } else {
        x += window.scrollX;
        y += window.scrollY;
    }

    // (-1, -1) indicates: leave position unchanged
    if (x !== -1 && y !== -1) {
        popup.style.left = x + 'px';
        popup.style.top = y + 'px';
        popup.style.display = '';
    }
}

function hidePopup() {
    let popup = document.getElementById('zhongwen-window');
    if (popup) {
        popup.style.display = 'none';
        popup.textContent = '';
    }
}

function highlightMatch(doc, rangeStartNode, rangeStartOffset, matchLen, selEndList) {
    if (!selEndList || selEndList.length === 0) return;

    let selEnd;
    let offset = rangeStartOffset + matchLen;

    for (let i = 0, len = selEndList.length; i < len; i++) {
        selEnd = selEndList[i];
        if (offset <= selEnd.offset) {
            break;
        }
        offset -= selEnd.offset;
    }

    let range = doc.createRange();
    range.setStart(rangeStartNode, rangeStartOffset);
    range.setEnd(selEnd.node, offset);

    let sel = window.getSelection();
    if (!sel.isCollapsed && selText !== sel.toString())
        return;
    sel.empty();
    sel.addRange(range);
    selText = sel.toString();
}

function clearHighlight() {

    if (selText === null) {
        return;
    }

    let selection = window.getSelection();
    if (selection.isCollapsed || selText === selection.toString()) {
        selection.empty();
    }
    selText = null;
}

function isVisible() {
    let popup = document.getElementById('zhongwen-window');
    return popup && popup.style.display !== 'none';
}

function getTextForClipboard() {
    let result = '';
    for (let i = 0; i < savedSearchResults.length; i++) {
        result += savedSearchResults[i].slice(0, -1).join('\t');
        result += '\n';
    }
    return result;
}

function makeDiv(input) {
    let div = document.createElement('div');

    div.id = 'zhongwenDiv';

    let text;
    if (input.value) {
        text = input.value;
    } else {
        text = '';
    }
    div.innerText = text;

    div.style.cssText = window.getComputedStyle(input, '').cssText;
    div.scrollTop = input.scrollTop;
    div.scrollLeft = input.scrollLeft;
    div.style.position = 'absolute';
    div.style.zIndex = 7000;
    $(div).offset({
        top: $(input).offset().top,
        left: $(input).offset().left
    });

    return div;
}

function findNextTextNode(root, previous) {
    if (root === null) {
        return null;
    }
    let nodeIterator = document.createNodeIterator(root, NodeFilter.SHOW_TEXT, null);
    let node = nodeIterator.nextNode();
    while (node !== previous) {
        node = nodeIterator.nextNode();
        if (node === null) {
            return findNextTextNode(root.parentNode, previous);
        }
    }
    let result = nodeIterator.nextNode();
    if (result !== null) {
        return result;
    } else {
        return findNextTextNode(root.parentNode, previous);
    }
}

function findPreviousTextNode(root, previous) {
    if (root === null) {
        return null;
    }
    let nodeIterator = document.createNodeIterator(root, NodeFilter.SHOW_TEXT, null);
    let node = nodeIterator.nextNode();
    while (node !== previous) {
        node = nodeIterator.nextNode();
        if (node === null) {
            return findPreviousTextNode(root.parentNode, previous);
        }
    }
    nodeIterator.previousNode();
    let result = nodeIterator.previousNode();
    if (result !== null) {
        return result;
    } else {
        return findPreviousTextNode(root.parentNode, previous);
    }
}

function copyToClipboard(data) {
    chrome.runtime.sendMessage({
        'type': 'copy',
        'data': data
    });

    showPopup('Copied to clipboard', null, -1, -1);
}

function makeHtml(result, showToneColors) {

    let entry;
    let html = '';
    let texts = [];
    let hanziClass;

    if (result === null) return '';

    for (let i = 0; i < result.data.length; ++i) {
        entry = result.data[i][0].match(/^([^\s]+?)\s+([^\s]+?)\s+\[(.*?)\]?\s*\/(.+)\//);
        if (!entry) continue;

        // Hanzi

        if (config.simpTrad === 'auto') {

            let word = result.data[i][1];

            hanziClass = 'w-hanzi';
            if (config.fontSize === 'small') {
                hanziClass += '-small';
            }
            html += '<span class="' + hanziClass + '">' + word + '</span>&nbsp;';

        } else {

            hanziClass = 'w-hanzi';
            if (config.fontSize === 'small') {
                hanziClass += '-small';
            }
            html += '<span class="' + hanziClass + '">' + entry[2] + '</span>&nbsp;';
            if (entry[1] !== entry[2]) {
                html += '<span class="' + hanziClass + '">' + entry[1] + '</span>&nbsp;';
            }

        }

        // Pinyin

        let pinyinClass = 'w-pinyin';
        if (config.fontSize === 'small') {
            pinyinClass += '-small';
        }
        let p = pinyinAndZhuyin(entry[3], showToneColors, pinyinClass);
        html += p[0];

        // Zhuyin

        if (config.zhuyin === 'yes') {
            html += '<br>' + p[2];
        }

        // Definition

        let defClass = 'w-def';
        if (config.fontSize === 'small') {
            defClass += '-small';
        }
        let translation = entry[4].replace(/\//g, ' ◆ ');
        html += '<br><span class="' + defClass + '">' + translation + '</span><br>';

        let addFinalBr = false;

        // Grammar
        if (config.grammar !== 'no' && result.grammar && result.grammar.index === i) {
            html += '<br><span class="grammar">Press "g" for grammar and usage notes.</span><br>';
            addFinalBr = true;
        }

        // Vocab
        if (config.vocab !== 'no' && result.vocab && result.vocab.index === i) {
            html += '<br><span class="vocab">Press "v" for vocabulary notes.</span><br>';
            addFinalBr = true;
        }

        if (addFinalBr) {
            html += '<br>';
        }

        texts[i] = [entry[2], entry[1], p[1], translation, entry[3]];
    }
    if (result.more) {
        html += '&hellip;<br/>';
    }

    savedSearchResults = texts;
    savedSearchResults.grammar = result.grammar;
    savedSearchResults.vocab = result.vocab;

    return html;
}

let tones = {
    1: '&#772;',
    2: '&#769;',
    3: '&#780;',
    4: '&#768;',
    5: ''
};

let utones = {
    1: '\u0304',
    2: '\u0301',
    3: '\u030C',
    4: '\u0300',
    5: ''
};

function parse(s) {
    return s.match(/([^AEIOU:aeiou]*)([AEIOUaeiou:]+)([^aeiou:]*)([1-5])/);
}

function tonify(vowels, tone) {
    let html = '';
    let text = '';

    if (vowels === 'ou') {
        html = 'o' + tones[tone] + 'u';
        text = 'o' + utones[tone] + 'u';
    } else {
        let tonified = false;
        for (let i = 0; i < vowels.length; i++) {
            let c = vowels.charAt(i);
            html += c;
            text += c;
            if (c === 'a' || c === 'e') {
                html += tones[tone];
                text += utones[tone];
                tonified = true;
            } else if (i === vowels.length - 1 && !tonified) {
                html += tones[tone];
                text += utones[tone];
                tonified = true;
            }
        }
        html = html.replace(/u:/, '&uuml;');
        text = text.replace(/u:/, '\u00FC');
    }

    return [html, text];
}

function pinyinAndZhuyin(syllables, showToneColors, pinyinClass) {
    let text = '';
    let html = '';
    let zhuyin = '';
    let a = syllables.split(/[\s·]+/);
    for (let i = 0; i < a.length; i++) {
        let syllable = a[i];

        // ',' in pinyin
        if (syllable === ',') {
            html += ' ,';
            text += ' ,';
            continue;
        }

        if (i > 0) {
            html += '&nbsp;';
            text += ' ';
            zhuyin += '&nbsp;';
        }
        if (syllable === 'r5') {
            if (showToneColors) {
                html += '<span class="' + pinyinClass + ' tone5">r</span>';
            } else {
                html += '<span class="' + pinyinClass + '">r</span>';
            }
            text += 'r';
            continue;
        }
        if (syllable === 'xx5') {
            if (showToneColors) {
                html += '<span class="' + pinyinClass + ' tone5">??</span>';
            } else {
                html += '<span class="' + pinyinClass + '">??</span>';
            }
            text += '??';
            continue;
        }
        let m = parse(syllable);
        if (showToneColors) {
            html += '<span class="' + pinyinClass + ' tone' + m[4] + '">';
        } else {
            html += '<span class="' + pinyinClass + '">';
        }
        let t = tonify(m[2], m[4]);
        html += m[1] + t[0] + m[3];
        html += '</span>';
        text += m[1] + t[1] + m[3];

        let zhuyinClass = 'w-zhuyin';
        if (config.fontSize === 'small') {
            zhuyinClass += '-small';
        }

        zhuyin += '<span class="tone' + m[4] + ' ' + zhuyinClass + '">'
            + globalThis.numericPinyin2Zhuyin(syllable) + '</span>';
    }
    return [html, text, zhuyin];
}

function printFirstWordDefinition() {
    if (!dictionary || !dictionary.wordDict) {
        console.log("Dictionary is not loaded.");
        return;
    }
    
    // Assuming each entry is on a new line and format is "word - definition"
    const entries = dictionary.wordDict.split('\n');
    const firstEntry = entries[0];
    const [word, definition] = firstEntry.split(' / '); // Adjust split logic based on actual format

    console.log(`Word: ${word}, Definition: ${definition}`);
}
printFirstWordDefinition();
console.log("no");




// Add mouse move listener to the document
document.addEventListener('mousemove', onMouseMove);

// Example of hiding the popup when the mouse leaves the document
document.addEventListener('mouseleave', hidePopup);