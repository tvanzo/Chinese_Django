'use strict';

let dictionary = null; // This will hold the loaded dictionary

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
let config = {
    css: 'white',
    tonecolors: 'no',
    fontSize: 'small',
    skritterTLD: 'com',
    zhuyin: 'no',
    grammar: 'yes',
    vocab: 'yes',
    simpTrad: 'classic',
    toneColorScheme: 'standard'
};

/* global globalThis */

const zhuyinTones = ['?', '', '\u02CA', '\u02C7', '\u02CB', '\u30FB'];

const pinyinTones = {
    1: '\u0304',
    2: '\u0301',
    3: '\u030C',
    4: '\u0300',
    5: ''
};

const zhuyinMap = {
    'a': '\u311a',
    'ai': '\u311e',
    'an': '\u3122',
    'ang': '\u3124',
    'ao': '\u3120',
    'ba': '\u3105\u311a',
    'bai': '\u3105\u311e',
    'ban': '\u3105\u3122',
    'bang': '\u3105\u3124',
    'bao': '\u3105\u3120',
    'bei': '\u3105\u311f',
    'ben': '\u3105\u3123',
    'beng': '\u3105\u3125',
    'bi': '\u3105\u3127',
    'bian': '\u3105\u3127\u3122',
    'biao': '\u3105\u3127\u3120',
    'bie': '\u3105\u3127\u311d',
    'bin': '\u3105\u3127\u3123',
    'bing': '\u3105\u3127\u3125',
    'bo': '\u3105\u311b',
    'bu': '\u3105\u3128',
    'ca': '\u3118\u311a',
    'cai': '\u3118\u311e',
    'can': '\u3118\u3122',
    'cang': '\u3118\u3124',
    'cao': '\u3118\u3120',
    'ce': '\u3118\u311c',
    'cen': '\u3118\u3123',
    'ceng': '\u3118\u3125',
    'cha': '\u3114\u311a',
    'chai': '\u3114\u311e',
    'chan': '\u3114\u3122',
    'chang': '\u3114\u3124',
    'chao': '\u3114\u3120',
    'che': '\u3114\u311c',
    'chen': '\u3114\u3123',
    'cheng': '\u3114\u3125',
    'chi': '\u3114',
    'chong': '\u3114\u3128\u3125',
    'chou': '\u3114\u3121',
    'chu': '\u3114\u3128',
    'chua': '\u3114\u3128\u311a',
    'chuai': '\u3114\u3128\u311e',
    'chuan': '\u3114\u3128\u3122',
    'chuang': '\u3114\u3128\u3124',
    'chui': '\u3114\u3128\u311f',
    'chun': '\u3114\u3128\u3123',
    'chuo': '\u3114\u3128\u311b',
    'ci': '\u3118',
    'cong': '\u3118\u3128\u3125',
    'cou': '\u3118\u3121',
    'cu': '\u3118\u3128',
    'cuan': '\u3118\u3128\u3122',
    'cui': '\u3118\u3128\u311f',
    'cun': '\u3118\u3128\u3123',
    'cuo': '\u3118\u3128\u311b',
    'da': '\u3109\u311a',
    'dai': '\u3109\u311e',
    'dan': '\u3109\u3122',
    'dang': '\u3109\u3124',
    'dao': '\u3109\u3120',
    'de': '\u3109\u311c',
    'dei': '\u3109\u311f',
    'den': '\u3109\u3123',
    'deng': '\u3109\u3125',
    'di': '\u3109\u3127',
    'dian': '\u3109\u3127\u3122',
    'diang': '\u3109\u3127\u3124',
    'diao': '\u3109\u3127\u3120',
    'die': '\u3109\u3127\u311d',
    'ding': '\u3109\u3127\u3125',
    'diu': '\u3109\u3127\u3121',
    'dong': '\u3109\u3128\u3125',
    'dou': '\u3109\u3121',
    'du': '\u3109\u3128',
    'duan': '\u3109\u3128\u3122',
    'dui': '\u3109\u3128\u311f',
    'dun': '\u3109\u3128\u3123',
    'duo': '\u3109\u3128\u311b',
    'e': '\u311c',
    'ei': '\u311f',
    'en': '\u3123',
    'er': '\u3126',
    'fa': '\u3108\u311a',
    'fan': '\u3108\u3122',
    'fang': '\u3108\u3124',
    'fei': '\u3108\u311f',
    'fen': '\u3108\u3123',
    'feng': '\u3108\u3125',
    'fo': '\u3108\u311b',
    'fou': '\u3108\u3121',
    'fu': '\u3108\u3128',
    'ga': '\u310d\u311a',
    'gai': '\u310d\u311e',
    'gan': '\u310d\u3122',
    'gang': '\u310d\u3124',
    'gao': '\u310d\u3120',
    'ge': '\u310d\u311c',
    'gei': '\u310d\u311f',
    'gen': '\u310d\u3123',
    'geng': '\u310d\u3125',
    'gong': '\u310d\u3128\u3125',
    'gou': '\u310d\u3121',
    'gu': '\u310d\u3128',
    'gua': '\u310d\u3128\u311a',
    'guai': '\u310d\u3128\u311e',
    'guan': '\u310d\u3128\u3122',
    'guang': '\u310d\u3128\u3124',
    'gui': '\u310d\u3128\u311f',
    'gun': '\u310d\u3128\u3123',
    'guo': '\u310d\u3128\u311b',
    'ha': '\u310f\u311a',
    'hai': '\u310f\u311e',
    'han': '\u310f\u3122',
    'hang': '\u310f\u3124',
    'hao': '\u310f\u3120',
    'he': '\u310f\u311c',
    'hei': '\u310f\u311f',
    'hen': '\u310f\u3123',
    'heng': '\u310f\u3125',
    'hong': '\u310f\u3128\u3125',
    'hou': '\u310f\u3121',
    'hu': '\u310f\u3128',
    'hua': '\u310f\u3128\u311a',
    'huai': '\u310f\u3128\u311e',
    'huan': '\u310f\u3128\u3122',
    'huang': '\u310f\u3128\u3124',
    'hui': '\u310f\u3128\u311f',
    'hun': '\u310f\u3128\u3123',
    'huo': '\u310f\u3128\u311b',
    'ji': '\u3110\u3127',
    'jia': '\u3110\u3127\u311a',
    'jian': '\u3110\u3127\u3122',
    'jiang': '\u3110\u3127\u3124',
    'jiao': '\u3110\u3127\u3120',
    'jie': '\u3110\u3127\u311d',
    'jin': '\u3110\u3127\u3123',
    'jing': '\u3110\u3127\u3125',
    'jiong': '\u3110\u3129\u3125',
    'jiu': '\u3110\u3127\u3121',
    'ju': '\u3110\u3129',
    'juan': '\u3110\u3129\u3122',
    'jue': '\u3110\u3129\u311d',
    'jun': '\u3110\u3129\u3123',
    'ka': '\u310e\u311a',
    'kai': '\u310e\u311e',
    'kan': '\u310e\u3122',
    'kang': '\u310e\u3124',
    'kao': '\u310e\u3120',
    'ke': '\u310e\u311c',
    'ken': '\u310e\u3123',
    'keng': '\u310e\u3125',
    'kong': '\u310e\u3128\u3125',
    'kou': '\u310e\u3121',
    'ku': '\u310e\u3128',
    'kua': '\u310e\u3128\u311a',
    'kuai': '\u310e\u3128\u311e',
    'kuan': '\u310e\u3128\u3122',
    'kuang': '\u310e\u3128\u3124',
    'kui': '\u310e\u3128\u311f',
    'kun': '\u310e\u3128\u3123',
    'kuo': '\u310e\u3128\u311b',
    'la': '\u310c\u311a',
    'lai': '\u310c\u311e',
    'lan': '\u310c\u3122',
    'lang': '\u310c\u3124',
    'lao': '\u310c\u3120',
    'le': '\u310c\u311c',
    'lei': '\u310c\u311f',
    'leng': '\u310c\u3125',
    'li': '\u310c\u3127',
    'lia': '\u310c\u3127\u311a',
    'lian': '\u310c\u3127\u3122',
    'liang': '\u310c\u3127\u3124',
    'liao': '\u310c\u3127\u3120',
    'lie': '\u310c\u3127\u311d',
    'lin': '\u310c\u3127\u3123',
    'ling': '\u310c\u3127\u3125',
    'liu': '\u310c\u3127\u3121',
    'lo': '\u310c\u311b',
    'long': '\u310c\u3128\u3125',
    'lou': '\u310c\u3121',
    'lu': '\u310c\u3128',
    'lu:': '\u310c\u3129',
    'luan': '\u310c\u3128\u3123',
    'lu:e': '\u310c\u3129\u311d',
    'lun': '\u310c\u3129',
    'lu:n': '\u310c\u3129\u3123',
    'luo': '\u310c\u3129\u3123',
    'ma': '\u3107\u311a',
    'mai': '\u3107\u311e',
    'man': '\u3107\u3122',
    'mang': '\u3107\u3124',
    'mao': '\u3107\u3120',
    'me': '\u3107\u311c',
    'mei': '\u3107\u311f',
    'men': '\u3107\u3123',
    'meng': '\u3107\u3125',
    'mi': '\u3107\u3127',
    'mian': '\u3107\u3127\u3122',
    'miao': '\u3107\u3127\u3120',
    'mie': '\u3107\u3127\u311d',
    'min': '\u3107\u3127\u3123',
    'ming': '\u3107\u3127\u3125',
    'miu': '\u3107\u3127\u3121',
    'mo': '\u3107\u311b',
    'mou': '\u3107\u3121',
    'mu': '\u3107\u3128',
    'na': '\u310b\u311a',
    'nai': '\u310b\u311e',
    'nan': '\u310b\u3122',
    'nang': '\u310b\u3124',
    'nao': '\u310b\u3120',
    'ne': '\u310b\u311c',
    'nei': '\u310b\u311f',
    'nen': '\u310b\u3123',
    'neng': '\u310b\u3125',
    'ni': '\u310b\u3127',
    'nia': '\u310b\u3127\u311a',
    'nian': '\u310b\u3127\u3122',
    'niang': '\u310b\u3127\u3124',
    'niao': '\u310b\u3127\u3120',
    'nie': '\u310b\u3127\u311d',
    'nin': '\u310b\u3127\u3123',
    'ning': '\u310b\u3127\u3125',
    'niu': '\u310b\u3127\u3121',
    'nong': '\u310b\u3128\u3125',
    'nou': '\u310b\u3121',
    'nu': '\u310b\u3128',
    'nu:': '\u310b\u3129',
    'nuan': '\u310b\u3128\u3123',
    'nu:e': '\u310b\u3129\u311d',
    'nun': '\u310b\u3129',
    'nuo': '\u310b\u3129\u311d',
    'ou': '\u3121',
    'pa': '\u3106\u311a',
    'pai': '\u3106\u311e',
    'pan': '\u3106\u3122',
    'pang': '\u3106\u3124',
    'pao': '\u3106\u3120',
    'pei': '\u3106\u311f',
    'pen': '\u3106\u3123',
    'peng': '\u3106\u3125',
    'pi': '\u3106\u3127',
    'pian': '\u3106\u3127\u3122',
    'piao': '\u3106\u3127\u3120',
    'pie': '\u3106\u3127\u311d',
    'pin': '\u3106\u3127\u3123',
    'ping': '\u3106\u3127\u3125',
    'po': '\u3106\u311b',
    'pou': '\u3106\u3121',
    'pu': '\u3106\u3128',
    'qi': '\u3111\u3127',
    'qia': '\u3111\u3127\u311a',
    'qian': '\u3111\u3127\u3122',
    'qiang': '\u3111\u3127\u3124',
    'qiao': '\u3111\u3127\u3120',
    'qie': '\u3111\u3127\u311d',
    'qin': '\u3111\u3127\u3123',
    'qing': '\u3111\u3127\u3125',
    'qiong': '\u3111\u3129\u3125',
    'qiu': '\u3111\u3127\u3121',
    'qu': '\u3111\u3129',
    'quan': '\u3111\u3129\u3122',
    'que': '\u3111\u3129\u311d',
    'qun': '\u3111\u3129\u3123',
    'ran': '\u3116\u3122',
    'rang': '\u3116\u3124',
    'rao': '\u3116\u3120',
    're': '\u3116\u311c',
    'ren': '\u3116\u3123',
    'reng': '\u3116\u3125',
    'ri': '\u3116',
    'rong': '\u3116\u3128\u3125',
    'rou': '\u3116\u3121',
    'ru': '\u3116\u3128',
    'ruan': '\u3116\u3128\u3122',
    'rui': '\u3116\u3128\u311f',
    'run': '\u3116\u3128\u3123',
    'ruo': '\u3116\u3128\u311b',
    'sa': '\u3119\u311a',
    'sai': '\u3119\u311e',
    'san': '\u3119\u3122',
    'sang': '\u3119\u3124',
    'sao': '\u3119\u3120',
    'se': '\u3119\u311c',
    'sei': '\u3119\u311f',
    'sen': '\u3119\u3123',
    'seng': '\u3119\u3125',
    'sha': '\u3115\u311a',
    'shai': '\u3115\u311e',
    'shan': '\u3115\u3122',
    'shang': '\u3115\u3124',
    'shao': '\u3115\u3120',
    'she': '\u3115\u311c',
    'shei': '\u3115\u311f',
    'shen': '\u3115\u3123',
    'sheng': '\u3115\u3125',
    'shi': '\u3115',
    'shong': '\u3115\u3128\u3125',
    'shou': '\u3115\u3121',
    'shu': '\u3115\u3128',
    'shua': '\u3115\u3128\u311a',
    'shuai': '\u3115\u3128\u311e',
    'shuan': '\u3115\u3128\u3122',
    'shuang': '\u3115\u3128\u3124',
    'shui': '\u3115\u3128\u311f',
    'shun': '\u3115\u3128\u3123',
    'shuo': '\u3115\u3128\u311b',
    'si': '\u3119',
    'song': '\u3119\u3128\u3125',
    'sou': '\u3119\u3121',
    'su': '\u3119\u3128',
    'suan': '\u3119\u3128\u3122',
    'sui': '\u3119\u3128\u311f',
    'sun': '\u3119\u3128\u3123',
    'suo': '\u3119\u3128\u311b',
    'ta': '\u310a\u311a',
    'tai': '\u310a\u311e',
    'tan': '\u310a\u3122',
    'tang': '\u310a\u3124',
    'tao': '\u310a\u3120',
    'te': '\u310a\u311c',
    'teng': '\u310a\u3125',
    'ti': '\u310a\u3127',
    'tian': '\u310a\u3127\u3122',
    'tiao': '\u310a\u3127\u3120',
    'tie': '\u310a\u3127\u311d',
    'ting': '\u310a\u3127\u3125',
    'tong': '\u310a\u3128\u3125',
    'tou': '\u310a\u3121',
    'tu': '\u310a\u3128',
    'tuan': '\u310a\u3128\u3122',
    'tui': '\u310a\u3128\u311f',
    'tun': '\u310a\u3128\u3123',
    'tuo': '\u310a\u3128\u311b',
    'wa': '\u3128\u311a',
    'wai': '\u3128\u311e',
    'wan': '\u3128\u3122',
    'wang': '\u3128\u3124',
    'wei': '\u3128\u311f',
    'wen': '\u3128\u3123',
    'weng': '\u3128\u3125',
    'wo': '\u3128\u311b',
    'wu': '\u3128',
    'xi': '\u3112\u3127',
    'xia': '\u3112\u3127\u311a',
    'xian': '\u3112\u3127\u3122',
    'xiang': '\u3112\u3127\u3124',
    'xiao': '\u3112\u3127\u3120',
    'xie': '\u3112\u3127\u311d',
    'xin': '\u3112\u3127\u3123',
    'xing': '\u3112\u3127\u3125',
    'xiong': '\u3112\u3129\u3125',
    'xiu': '\u3112\u3127\u3121',
    'xu': '\u3112\u3129',
    'xuan': '\u3112\u3129\u3122',
    'xue': '\u3112\u3129\u311d',
    'xun': '\u3112\u3129\u3123',
    'ya': '\u3127\u311a',
    'yan': '\u3127\u3122',
    'yang': '\u3127\u3124',
    'yao': '\u3127\u3120',
    'ye': '\u3127\u311d',
    'yi': '\u3127',
    'yin': '\u3127\u3123',
    'ying': '\u3127\u3125',
    'yong': '\u3129\u3125',
    'you': '\u3127\u3121',
    'yu': '\u3129',
    'yuan': '\u3129\u3122',
    'yue': '\u3129\u311d',
    'yun': '\u3129\u3123',
    'za': '\u3117\u311a',
    'zai': '\u3117\u311e',
    'zan': '\u3117\u3122',
    'zang': '\u3117\u3124',
    'zao': '\u3117\u3120',
    'ze': '\u3117\u311c',
    'zei': '\u3117\u311f',
    'zen': '\u3117\u3123',
    'zeng': '\u3117\u3125',
    'zha': '\u3113\u311a',
    'zhai': '\u3113\u311e',
    'zhan': '\u3113\u3122',
    'zhang': '\u3113\u3124',
    'zhao': '\u3113\u3120',
    'zhe': '\u3113\u311c',
    'zhei': '\u3113\u311f',
    'zhen': '\u3113\u3123',
    'zheng': '\u3113\u3125',
    'zhi': '\u3113',
    'zhong': '\u3113\u3128\u3125',
    'zhou': '\u3113\u3121',
    'zhu': '\u3113\u3128',
    'zhua': '\u3113\u3128\u311a',
    'zhuai': '\u3113\u3128\u311e',
    'zhuan': '\u3113\u3128\u3122',
    'zhuang': '\u3113\u3128\u3124',
    'zhui': '\u3113\u3128\u311f',
    'zhun': '\u3113\u3128\u3123',
    'zhuo': '\u3113\u3128\u311b',
    'zi': '\u3117',
    'zong': '\u3117\u3128\u3125',
    'zou': '\u3117\u3121',
    'zu': '\u3117\u3128',
    'zuan': '\u3117\u3128\u3122',
    'zui': '\u3117\u3128\u311f',
    'zun': '\u3117\u3128\u3123',
    'zuo': '\u3117\u3128\u311b'
};

globalThis.numericPinyin2Zhuyin = function (syllable) {
    return zhuyinMap[syllable.substring(0, syllable.length - 1).toLowerCase()]
        + zhuyinTones[syllable[syllable.length - 1]] + '</span>';

};

globalThis.accentedPinyin2Zhuyin = function (syllable) {
    let lowerCased = syllable.toLowerCase();
    let key = lowerCased;
    let tone = 5;
    for (let i = 1; i <= 4; i++) {
        let idx = lowerCased.indexOf(pinyinTones[i]);
        if (idx > 0) {
            key = lowerCased.substring(0, idx);
            if (idx < lowerCased.length -1) {
                key += lowerCased.substring(idx + 1);
            }
            tone = i;
            break;
        }
    }
    return zhuyinMap[key] + zhuyinTones[tone];
};



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
}

function search(text) {

    if (!dictionary) {
        // dictionary not loaded
        return;
    }

    let entry = dictionary.wordSearch(text);

    if (entry) {
        for (let i = 0; i < entry.data.length; i++) {
            let word = entry.data[i][1];
            if (dictionary.hasGrammarKeyword(word) && (entry.matchLen === word.length)) {
                // the final index should be the last one with the maximum length
                entry.grammar = { keyword: word, index: i };
            }
            if (dictionary.hasVocabKeyword(word) && (entry.matchLen === word.length)) {
                // the final index should be the last one with the maximum length
                entry.vocab = { keyword: word, index: i };
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
    console.log("Dictionary loaded successfully!");
}
// Execute the loadDictionary function when the document is fully loaded
document.addEventListener('DOMContentLoaded', async () => {
console.log("Dictionary loading inner...");
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
        console.log(wordData); // Replace this with your actual popup display logic
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
    if (!popup) initPopup();
    popup.innerHTML = html;
    let rect = popup.getBoundingClientRect();
    let winWidth = window.innerWidth;
    let winHeight = window.innerHeight;

    // Adjust position to prevent overflow
    if (x + rect.width > winWidth) x -= rect.width;
    if (y + rect.height > winHeight) y -= rect.height;

    popup.style.left = `${x}px`;
    popup.style.top = `${y}px`;
    popup.classList.add('show'); // Use class for showing the popup
}


// Testing the popup




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

    if (!rangeNode) {
        clearHighlight();
        hidePopup();
        return;
    }

    if (selStartOffset < 0 || rangeNode.data.length <= selStartOffset) {
        clearHighlight();
        hidePopup();
        return;
    }

    let u = rangeNode.data.charCodeAt(selStartOffset);
    let isChineseCharacter = (
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
        return;
    }

    let selEndList = [];
    let originalText = getText(rangeNode, selStartOffset, selEndList, 30);

    // Remove zero-width non-joiner &zwnj;
    let text = originalText.replace(/\u200c/g, '');

    savedSelStartOffset = selStartOffset;
    savedSelEndList = selEndList;

    // Directly invoke search and process its result
    let searchResult = search(text);
    if (searchResult) {
        // Assuming search() is synchronous or you adapt it to return a promise and use .then()
        searchResult.originalText = originalText; // Emulate the extension's behavior
        processSearchResult(searchResult);
    }
}




function processSearchResult(result) {
     console.log("processSearchResult called with result:", result);
    
    // No need to check config existence here since we've directly initialized it
    const tonecolors = config.tonecolors; // Directly use it

    let selStartOffset = savedSelStartOffset;
    let selEndList = savedSelEndList;

    if (!result) {
        hidePopup();
        clearHighlight();
        return;
    }

    let highlightLength;
    let index = 0;
    for (let i = 0; i < result.matchLen; i++) {
        // Google Docs workaround: determine the correct highlight length
        while (result.originalText[index] === '\u200c') {
            index++;
        }
        index++;
    }
    highlightLength = index;

    selStartIncrement = result.matchLen;
    selStartDelta = (selStartOffset - savedRangeOffset);

    let rangeNode = savedRangeNode;
    // don't try to highlight form elements
    if (!('form' in savedTarget)) {
        let doc = rangeNode.ownerDocument;
        if (!doc) {
            clearHighlight();
            hidePopup();
            return;
        }
        highlightMatch(doc, rangeNode, selStartOffset, highlightLength, selEndList);
    }

    showPopup(makeHtml(result, tonecolors !== 'no'), savedTarget, popX, popY, false);
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

    // Use innerHTML instead of jQuery's html() method
    popup.innerHTML = html;

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








// Add mouse move listener to the document
document.addEventListener('mousemove', onMouseMove);

// Example of hiding the popup when the mouse leaves the document
document.addEventListener('mouseleave', hidePopup);
