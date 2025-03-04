"use client";
import { useState } from "react";
import type React from "react";

import { motion } from "framer-motion";
import { ArrowUp, Loader2, Database, Info, Check } from "lucide-react";
import type { Message } from "./types";
import ResponseFormatter from "./ResponseFormatter";

const dataSources = [
  "PostgreSQL",
  "Databricks",
  "Redshift",
  "Snowflake",
  "MySQL",
  "BigQuery",
  "RDS",
];

export default function DatabaseInterface() {
  const [step, setStep] = useState(0);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [dbname, setDbname] = useState("");
  const [user, setUser] = useState("");
  const [password, setPassword] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isLoadingSchema, setIsLoadingSchema] = useState(false);
  const [isLoadingVector, setIsLoadingVector] = useState(false);
  const [vectorLoaded, setVectorLoaded] = useState(false);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);
  const [schemaLoaded, setSchemaLoaded] = useState(false);
  const [metadataLoaded, setMetadataLoaded] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleSelectSource = (source: string) => {
    setSelectedSource(source);
    setStep(1);
  };

  const handleTestConnection = async () => {
    setIsLoading(true);
    setError("");

    const url = `http://localhost:8000/connect-postgres/?dbname=${dbname}&user=${user}&password=${password}&host=${host}&port=${port}`;
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
      });
      const data = await response.json();

      if (
        response.ok &&
        data.message === "Database connection to Postgres successful"
      ) {
        setIsConnected(true);
        setStep(2);
      } else {
        setError(data.message || "Connection failed");
      }
    } catch (error) {
      setError("Failed to connect to database. Please check your credentials.");
      console.error("Connection failed", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadSchema = async () => {
    setIsLoadingSchema(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/load-schema/", {
        method: "POST",
        headers: {
          accept: "application/json",
        },
        body: "",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();
      setSchemaLoaded(true);
    } catch (error) {
      setError("Failed to load schema. Please try again.");
      console.error("Schema loading failed:", error);
    } finally {
      setIsLoadingSchema(false);
    }
  };

  const createVectorDB = async () => {
    setIsLoadingVector(true);
    setError("");

    try {
      const response = await fetch(
        "http://localhost:8000/create-vector-store",
        {
          method: "POST",
          headers: {
            accept: "application/json",
          },
          body: "",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();
      setVectorLoaded(true);
    } catch (error) {
      setError("Failed to Create Vector. Please try again.");
      console.error("Vector loading failed:", error);
    } finally {
      setIsLoadingVector(false);
    }
  };

  const handleLoadMetadata = async () => {
    setIsLoadingMetadata(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/load-metadata/", {
        method: "POST",
        headers: {
          accept: "application/json",
        },
        body: "",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();
      setMetadataLoaded(true);
    } catch (error) {
      setError("Failed to load metadata. Please try again.");
      console.error("Metadata loading failed:", error);
    } finally {
      setIsLoadingMetadata(false);
    }
  };

  const handleSubmitMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    setIsLoading(true);
    setError("");

    const userMessage: Message = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    let accumulatedResponse = "";

    try {
      const response = await fetch(
        `http://localhost:8000/generate-query/?query_text=${encodeURIComponent(
          message
        )}`,
        {
          method: "POST",
          headers: {
            accept: "application/json",
          },
          body: "",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.text();
      const jsonStrings = data.match(/\{[^}]+\}/g) || [];

      for (const jsonString of jsonStrings) {
        try {
          const jsonData = JSON.parse(jsonString);
          if (jsonData.event === "status" || jsonData.event === "sql_query") {
            accumulatedResponse += "\n" + jsonData.data;
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];

              if (lastMessage?.role === "assistant") {
                newMessages[newMessages.length - 1] = {
                  ...lastMessage,
                  content: accumulatedResponse.trim(),
                };
              } else {
                newMessages.push({
                  role: "assistant",
                  content: accumulatedResponse.trim(),
                  timestamp: new Date().toISOString(),
                });
              }
              return newMessages;
            });
          } else if (jsonData.event === "error") {
            setError(jsonData.data);
          }
        } catch (e) {
          console.error("Error parsing JSON:", e);
        }
      }
    } catch (error) {
      console.error("Failed to fetch:", error);
      setError(
        error instanceof Error
          ? error.message
          : "Failed to send message. Please try again."
      );
    } finally {
      setIsLoading(false);
    }

    setMessage("");
  };

  return (
    <div className="bg-[#212121] min-h-screen w-screen flex flex-col">
      {/* Welcome Screen */}
      {step === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
          className="flex-1 flex flex-col items-center justify-center p-4 text-white"
        >
          <h1 className="text-3xl font-bold mb-8">Welcome aboard! 🚀</h1>
          <p className="text-xl mb-8">
            Let's get started by connecting your data source.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {dataSources.map((source) => (
              <motion.button
                key={source}
                onClick={() => handleSelectSource(source)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                disabled={source !== "PostgreSQL"}
                className={`px-6 py-3 rounded-lg shadow-lg text-white transition-colors
                  ${
                    source === "PostgreSQL"
                      ? "bg-[#303030] hover:bg-[#404040]"
                      : "bg-gray-600 opacity-50 cursor-not-allowed"
                  }`}
              >
                {source}
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Database Connection Form */}
      {step === 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="flex-1 flex items-center justify-center p-4"
        >
          <div className="bg-[#303030] p-8 rounded-xl shadow-xl text-white max-w-md w-full">
            <h2 className="text-2xl mb-6">Connect to {selectedSource}</h2>
            {error && (
              <div className="mb-4 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
                {error}
              </div>
            )}
            <div className="space-y-4">
              <input
                type="text"
                value={dbname}
                onChange={(e) => setDbname(e.target.value)}
                placeholder="Database Name"
                className="w-full p-3 bg-transparent border border-white/20 rounded-lg outline-none focus:border-white/40 transition-colors"
              />
              <input
                type="text"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                placeholder="User"
                className="w-full p-3 bg-transparent border border-white/20 rounded-lg outline-none focus:border-white/40 transition-colors"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full p-3 bg-transparent border border-white/20 rounded-lg outline-none focus:border-white/40 transition-colors"
              />
              <input
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="Host"
                className="w-full p-3 bg-transparent border border-white/20 rounded-lg outline-none focus:border-white/40 transition-colors"
              />
              <input
                type="text"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="Port"
                className="w-full p-3 bg-transparent border border-white/20 rounded-lg outline-none focus:border-white/40 transition-colors"
              />
              <button
                onClick={handleTestConnection}
                disabled={isLoading}
                className="w-full p-3 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  "Test Connection"
                )}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Schema and Metadata Loader */}
      {step === 2 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="flex-1 flex items-center justify-center p-4"
        >
          <div className="bg-[#303030] p-8 rounded-xl shadow-xl text-white max-w-md w-full">
            <h2 className="text-2xl mb-6">Load Schema and Metadata</h2>
            {error && (
              <div className="mb-4 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
                {error}
              </div>
            )}
            <div className="space-y-4">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="w-full p-3 bg-[#404040] text-white rounded-lg font-medium hover:bg-[#505050] transition-colors flex items-center justify-between"
              >
                <span>Settings</span>
                <span>{showSettings ? "▲" : "▼"}</span>
              </button>
              {showSettings && (
                <>
                  <button
                    onClick={handleLoadSchema}
                    disabled={isLoadingSchema}
                    className="w-full p-3 bg-[#404040] text-white rounded-lg font-medium hover:bg-[#505050] transition-colors flex items-center justify-center gap-2"
                  >
                    {isLoadingSchema ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Loading Schema...
                      </>
                    ) : (
                      <>
                        <Database className="w-5 h-5" />
                        Load Schema
                      </>
                    )}
                    {!isLoadingSchema && schemaLoaded && (
                      <Check className="w-5 h-5 text-green-500" />
                    )}
                  </button>
                  <button
                    onClick={handleLoadMetadata}
                    disabled={isLoadingMetadata}
                    className="w-full p-3 bg-[#404040] text-white rounded-lg font-medium hover:bg-[#505050] transition-colors flex items-center justify-center gap-2"
                  >
                    {isLoadingMetadata ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Loading Metadata...
                      </>
                    ) : (
                      <>
                        <Info className="w-5 h-5" />
                        Load Metadata
                      </>
                    )}
                    {!isLoadingMetadata && metadataLoaded && (
                      <Check className="w-5 h-5 text-green-500" />
                    )}
                  </button>
                  <button
                    onClick={createVectorDB}
                    disabled={isLoadingVector}
                    className="w-full p-3 bg-[#404040] text-white rounded-lg font-medium hover:bg-[#505050] transition-colors flex items-center justify-center gap-2"
                  >
                    {isLoadingVector ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Loading Vector...
                      </>
                    ) : (
                      <>
                        <Database className="w-5 h-5" />
                        Load Vector
                      </>
                    )}
                    {!isLoadingVector && vectorLoaded && (
                      <Check className="w-5 h-5 text-green-500" />
                    )}
                  </button>
                </>
              )}
              <button
                onClick={() => setStep(3)}
                className="w-full p-3 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition-colors"
              >
                Continue
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Chat Interface */}
      {step === 3 && (
        <div className="flex flex-col h-screen">
          {/* Chat Messages */}
          <div className="flex-1 overflow-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-3xl mx-auto flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`p-4 rounded-lg shadow-md ${
                    msg.role === "user"
                      ? "bg-[#303030] text-white"
                      : "bg-[#1e1e1e] text-white"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <ResponseFormatter content={msg.content} />
                  ) : (
                    <div className="whitespace-pre-wrap font-sans">
                      {msg.content}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="max-w-3xl mx-auto"
              >
                <div className="bg-red-500/20 p-4 rounded-lg text-red-200">
                  {error}
                </div>
              </motion.div>
            )}
          </div>

          {/* Message Input */}
          <motion.form
            onSubmit={handleSubmitMessage}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="p-4 border-t border-white/10 bg-[#202020]"
          >
            <div className="max-w-4xl mx-auto space-y-4">
              {/* Schema and Metadata Status */}
              <div className="flex justify-end space-x-4 text-sm text-white/70">
                <span>
                  Schema: {schemaLoaded ? "Loaded ✅" : "Not Loaded ❌"}
                </span>
                <span>
                  Metadata: {metadataLoaded ? "Loaded ✅" : "Not Loaded ❌"}
                </span>
                <span>
                  Vector: {vectorLoaded ? "Loaded ✅" : "Not Loaded ❌"}
                </span>
              </div>

              {/* Message Input and Send Button */}
              <div className="flex gap-4">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask a question..."
                  disabled={isLoading}
                  className="flex-1 bg-[#303030] text-white rounded-lg px-4 py-3 outline-none"
                />
                <button
                  type="submit"
                  disabled={isLoading || !message.trim()}
                  className="bg-white text-black px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <ArrowUp className="w-5 h-5" />
                      Send
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.form>
        </div>
      )}
    </div>
  );
}
