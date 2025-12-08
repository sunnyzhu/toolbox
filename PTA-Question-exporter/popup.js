document.getElementById('btn-extract').addEventListener('click', async () => {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = "正在处理...";
    statusDiv.style.color = "#666";

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: extractPTAData
    }, async (results) => {
        if (chrome.runtime.lastError) {
            statusDiv.textContent = "❌ 无法连接到页面";
            return;
        }

        const result = results[0]?.result;
        if (!result) {
             statusDiv.textContent = "❌ 未获取到数据";
             return;
        }

        if (result.success) {
            try {
                await navigator.clipboard.writeText(result.markdown);
                statusDiv.textContent = "✅ 成功！Markdown 已复制到剪贴板。";
                statusDiv.style.color = "green"; 
            } catch (clipboardErr) {
                statusDiv.textContent = "❌ 剪贴板写入失败: " + clipboardErr.message;
            }
        } else {
            statusDiv.textContent = "❌ " + result.error;
            statusDiv.style.color = "red";
        }
    });
});

async function extractPTAData() {
    try {
        // --- 1. URL 解析 ---
        const currentUrl = window.location.href;
        const psMatch = currentUrl.match(/problem-sets\/(\d+)/);
        const pMatch = currentUrl.match(/problemSetProblemId=(\d+)/);

        if (!psMatch || !pMatch) {
            return { success: false, error: "URL无效，请在题目详情页使用" };
        }

        const problemSetId = psMatch[1];
        const problemId = pMatch[1];

        // --- 2. API 请求 ---
        const problemApi = `https://pintia.cn/api/problem-sets/${problemSetId}/exam-problems/${problemId}`;
        const answerApi = `https://pintia.cn/api/problem-sets/problems/${problemId}/exam-draft`;

        const reqOptions = {
            method: 'GET',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
            }
        };

        const safeJson = async (res, name) => {
            if (!res.ok) throw new Error(`${name} API状态码: ${res.status}`);
            const text = await res.text();
            try { return JSON.parse(text); }
            catch (e) { throw new Error(`${name} 数据格式错误`); }
        };

        const [probRes, ansRes] = await Promise.all([
            fetch(problemApi, reqOptions),
            fetch(answerApi, reqOptions)
        ]);

        const probData = await safeJson(probRes, "题目");
        const ansData = await safeJson(ansRes, "答案");

        // --- 3. 提取数据 ---
        const pInfo = probData.problemSetProblem || {};
        const title = pInfo.title || "无标题";
        const label = pInfo.label || "0-0";
        const score = pInfo.score || 0;
        
        let contentRaw = pInfo.content || pInfo.problemConfig?.programmingProblemConfig?.content || "(题目内容提取为空)";
        let programCode = ansData.answer?.detail?.programmingSubmissionDetail?.program || "// 未找到保存的代码";

        const today = new Date().toISOString().split('T')[0];
        
        // --- 4. 智能格式清洗函数 (核心修改) ---
        function formatMarkdownContent(raw) {
            if (!raw) return "";

            // 正则说明：
            // (```[\s\S]*?```) : 捕获所有的代码块（包含反引号）
            // 我们通过 split 将文本切分为 [普通文本, 代码块, 普通文本, 代码块...]
            const parts = raw.split(/(```[\s\S]*?```)/g);

            const processedParts = parts.map(part => {
                // 如果是代码块 (以 ``` 开头)
                if (part.startsWith('```')) {
                    // 提取语言和内容
                    // 匹配 ```lang\n content ```
                    const match = part.match(/^```(\w*)\n?([\s\S]*?)```$/);
                    if (match) {
                        const lang = match[1] || "";
                        // 1. 去除首尾空白 (trim) 防止空行
                        // 2. 保持内部换行不动 (不转为双换行)
                        // 3. 绝对不要转义 * 号
                        const codeContent = match[2].trim();
                        return "```" + lang + "\n" + codeContent + "\n```";
                    }
                    return part; // 匹配失败则原样返回
                } else {
                    // 如果是普通文本
                    return part
                        .replace(/\*/g, '\\*')     // 仅在普通文本中转义星号
                        .replace(/\n+/g, '\n');  // 仅在普通文本中合并空行
                }
            });

            // 重新组合，并清理连接处的多余换行
            return processedParts.join('\n\n').replace(/\n{3,}/g, '\n\n').trim();
        }

        const processedContent = formatMarkdownContent(contentRaw);
        const processedCode = programCode.trim();

        // --- 5. 组装 Markdown ---
        const markdown = 
`# ${title}
---
tags:
created: "${today}"
type:
  - errorlog
course:
  - CSIntro
EL-source:
  - OJ-assignment
EL-QN: ${label}
EL-grade: ${score}
difficulty:
  - 1-easy
category:
priority:
  - 3-normal
---
## Question
[${title}](https://pintia.cn/problem-sets/${problemSetId}/exam/problems/type/7?problemSetProblemId=${problemId})
${processedContent}

## Answer
\`\`\`C
${processedCode}
\`\`\`

## Analysis
`;

        return { success: true, markdown: markdown };

    } catch (err) {
        return { success: false, error: err.message };
    }
}