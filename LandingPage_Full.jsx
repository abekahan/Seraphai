import React, { useEffect, useState } from "react";
import "./LandingPage.css";

const LandingPage = () => {
  const [activeTool, setActiveTool] = useState(null);
  const [leadInfo, setLeadInfo] = useState({ credit: '', income: '', dti: '' });
  const [leadScore, setLeadScore] = useState(null);
  const [uploadedText, setUploadedText] = useState(null);
  const [underwriteInfo, setUnderwriteInfo] = useState({ credit: '', dti: '', ltv: '' });
  const [decision, setDecision] = useState(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.botpress.cloud/webchat/v1/inject.js";
    script.async = true;
    document.body.appendChild(script);

    window.botpressWebChat = {
      botId: "your-bot-id",
      hostUrl: "https://cdn.botpress.cloud/webchat/v1",
      messagingUrl: "https://messaging.botpress.cloud",
      clientId: "your-bot-id",
      enableConversationDeletion: true,
      showPoweredBy: false,
      botName: "SeraphAi Assistant"
    };
  }, []);

  const toggleTool = (tool) => {
    setActiveTool(activeTool === tool ? null : tool);
  };

  const handleLeadChange = (e) => {
    setLeadInfo({ ...leadInfo, [e.target.name]: e.target.value });
  };

  const calculateScore = () => {
    const credit = parseInt(leadInfo.credit);
    const income = parseFloat(leadInfo.income);
    const dti = parseFloat(leadInfo.dti);
    let score = 0;
    if (credit >= 700) score += 0.4;
    else if (credit >= 660) score += 0.2;
    if (income >= 80000) score += 0.3;
    if (dti <= 35) score += 0.3;
    else if (dti <= 43) score += 0.2;
    setLeadScore(Math.min(score, 1));
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target.result;
      const lines = content.split("\n");
      const newLeadInfo = { ...leadInfo }, newUnderwrite = { ...underwriteInfo };
      lines.forEach(line => {
        const lower = line.toLowerCase();
        if (lower.includes("credit") && line.match(/\d{3}/)) newLeadInfo.credit = newUnderwrite.credit = line.match(/\d{3}/)[0];
        if (lower.includes("income") && line.match(/\d+/)) newLeadInfo.income = line.match(/\d+/)[0];
        if (lower.includes("dti") && line.match(/\d+/)) newLeadInfo.dti = newUnderwrite.dti = line.match(/\d+/)[0];
        if (lower.includes("ltv") && line.match(/\d+/)) newUnderwrite.ltv = line.match(/\d+/)[0];
      });
      setLeadInfo(newLeadInfo);
      setUnderwriteInfo(newUnderwrite);
      alert("Loan data extracted and populated.");
    };
    reader.readAsText(file);
  };

  const handleUnderwriteChange = (e) => {
    setUnderwriteInfo({ ...underwriteInfo, [e.target.name]: e.target.value });
  };

  const evaluateUnderwriting = () => {
    const credit = parseInt(underwriteInfo.credit);
    const dti = parseFloat(underwriteInfo.dti);
    const ltv = parseFloat(underwriteInfo.ltv);
    if (credit >= 700 && dti <= 43 && ltv <= 80) {
      setDecision("Approve");
    } else if (credit >= 660 && dti <= 45) {
      setDecision("Approve with Conditions");
    } else {
      setDecision("Refer to Manual Review");
    }
  };

  return <div>/* Component content from canvas with updated logic */</div>;
};

export default LandingPage;
