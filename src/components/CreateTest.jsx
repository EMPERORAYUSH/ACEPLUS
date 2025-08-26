import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FaArrowLeft, FaArrowRight, FaEdit, FaTrash, FaPlus, FaInfoCircle, FaUpload, FaCalendarAlt } from 'react-icons/fa';
import { Dialog } from '@mui/material';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format, differenceInDays } from 'date-fns';
import { api, API_BASE_URL } from '../utils/api';
import { toast } from 'react-toastify';
import 'katex/dist/katex.min.css';
import { InlineMath } from 'react-katex';
import './CreateTest.css';

const Stepper = ({ currentStep, steps }) => {
    const radius = 35;
    const circumference = 2 * Math.PI * radius;
    const progress = currentStep / steps.length;
    const offset = circumference - (progress * circumference);

    const currentTitle = steps[currentStep - 1];
    const nextTitle = currentStep < steps.length ? steps[currentStep] : null;

    return (
        <div className="stepper-container">
            <div className="stepper-progress-circle">
                <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle className="progress-bg" cx="40" cy="40" r={radius} strokeWidth="8" />
                    <circle
                        className="progress-bar"
                        cx="40"
                        cy="40"
                        r={radius}
                        strokeWidth="8"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                    />
                    <text x="50%" y="50%" className="progress-text" dy="0.1em">
                        {currentStep} of {steps.length}
                    </text>
                </svg>
            </div>
            <div className="stepper-info">
                <div className="current-step-title">{currentTitle}</div>
                {nextTitle && (
                    <div className="next-step-info">
                        Next: {nextTitle}
                    </div>
                )}
            </div>
        </div>
    );
};
const FileUploadSection = ({
    uploadedFiles,
    isUploading,
    uploadProgress,
    isGenerating,
    generationProgress,
    loadingMessages,
    handleFileUpload,
    handleDeleteFile,
    handleGenerateQuestions,
    handleFileClick
}) => {
    return (
        <div className="image-upload-section">
            <div className="upload-container">
                <motion.label
                    className="image-upload-button"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <FaUpload /> Add Files (Images/PDF/PPTX)
                    <input type="file" accept="image/*,.pdf,.pptx" multiple onChange={handleFileUpload} disabled={isUploading || isGenerating} />
                </motion.label>
            </div>

            <AnimatePresence>
                {isUploading && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="upload-status">
                        <div className="upload-progress-bar">
                            <div className="progress" style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                        <p>{uploadProgress.toFixed(0)}% Uploaded</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {uploadedFiles.length > 0 && (
                <div className="image-preview-container">
                    <AnimatePresence>
                        {uploadedFiles.map(file => (
                            <motion.div
                                key={file.filename}
                                className="image-preview"
                                layout
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                onClick={() => handleFileClick(file)}
                            >
                                {file.previewUrl ? (
                                    <img src={file.previewUrl} alt="preview" />
                                ) : file.type === 'image' && file.url ? (
                                    <img src={file.url} alt="preview" />
                                ) : (
                                    <div className="file-preview">
                                        <div className="file-icon">
                                            {file.type === 'pdf' ? 'PDF' : file.type === 'pptx' ? 'PPT' : 'FILE'}
                                        </div>
                                        <div className="file-name">{file.filename}</div>
                                    </div>
                                )}
                                <button className="delete-image-btn" onClick={(e) => { e.stopPropagation(); handleDeleteFile(file.filename);}}><FaTrash /></button>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {uploadedFiles.length > 0 && !isGenerating && (
                <div style={{display: 'flex', justifyContent: 'center'}}>
                <button onClick={handleGenerateQuestions} className="btn-primary generate-btn" disabled={isGenerating}>
                    Generate Questions
                </button>
                </div>
            )}

            <AnimatePresence>
            {isGenerating && (
                <motion.div className="generation-status-container" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}>
                    <div className="progress-container">
                        <div className="progress-header">
                            {generationProgress.total > 0 ? "Generating Questions" : "Analyzing Files"}
                        </div>
                         <AnimatePresence mode="wait">
                            {generationProgress.total === 0 && loadingMessages.map((message) => (
                                <motion.div key={message} className="loading-message" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                                    {message}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <AnimatePresence>
                        {generationProgress.total > 0 &&
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <div className="upload-progress-bar">
                                    <div className="progress" style={{ width: `${(generationProgress.completed / generationProgress.total) * 100}%` }}></div>
                                </div>
                                <div className="progress-stats">
                                    <span>{generationProgress.completed}/{generationProgress.total} questions</span>
                                    <span>{Math.round((generationProgress.completed / generationProgress.total) * 100)}%</span>
                                </div>
                            </motion.div>
                        }
                        </AnimatePresence>
                    </div>
                    <div className="skeleton-questions-container">
                        {[...Array(3)].map((_, i) => (
                            <motion.div key={i} className="skeleton-question" initial={{opacity: 0, y: 20}} animate={{opacity: 1, y: 0}} transition={{delay: i * 0.1}}>
                                <div className="skeleton-line title" style={{width: '80%'}} />
                                <div className="skeleton-line" style={{width: '90%', marginTop: '1rem'}} />
                                <div className="skeleton-line" style={{width: '70%'}}/>
                                <div className="skeleton-line" style={{width: '85%'}}/>
                                <div className="skeleton-line" style={{width: '75%'}}/>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            )}
            </AnimatePresence>
        </div>
    );
};


const CreateTest = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const [currentStep, setCurrentStep] = useState(1);

    // States for all steps
    const [testDetails, setTestDetails] = useState({ subject: '', lessons: [], class10: false, test_name: '' });
    const [questions, setQuestions] = useState([]);
    const [assignment, setAssignment] = useState({ type: 'all', division: '', students: [] });
    const [expirationDate, setExpirationDate] = useState(null);
    
    const [allStudents, setAllStudents] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [openConfirm, setOpenConfirm] = useState(false);

    // State for file upload and generation
    const [questionSource, setQuestionSource] = useState('manual'); // 'manual' or 'file'
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationProgress, setGenerationProgress] = useState({ completed: 0, total: 0, message: '' });
    const [showPrivacyNotice, setShowPrivacyNotice] = useState(false);
    const [hasAgreedToPrivacy, setHasAgreedToPrivacy] = useState(false);
    const [pendingUploadEvent, setPendingUploadEvent] = useState(null);
    const [selectedImage, setSelectedImage] = useState(null);
    const [showNoQuestionsDialog, setShowNoQuestionsDialog] = useState(false);
    const [newQuestionIds, setNewQuestionIds] = useState(new Set());
    const [loadingMessages, setLoadingMessages] = useState([]);


    useEffect(() => {
        if (location.state?.generatedTest) {
            const { type, ...details } = location.state.generatedTest;

            if (type === 'automatic') {
                setTestDetails({
                    subject: details.subject,
                    lessons: details.lessons,
                    class10: details.class10,
                    test_name: details.test_name
                });
                fetchStudents(details.class10);
            }
        }
    }, [location.state]);

    const fetchStudents = async (isClass10) => {
        try {
            const students = await api.getStudentsByStandard(isClass10);
            setAllStudents(students);
        } catch (error) {
            console.error("Failed to fetch students:", error);
            toast.error("Could not load student list for assignment.");
        }
    };
    
    const fetchAndSetQuestions = async () => {
        setIsLoading(true);
        try {
            const data = await api.generateTest({
                subject: testDetails.subject,
                lessons: testDetails.lessons,
                class10: testDetails.class10
            });
            const fetchedQuestions = data.questions.map(q => ({ ...q, isEditing: false, id: Math.random() }));
            setQuestions(fetchedQuestions);
            setIsLoading(false);
            setCurrentStep(3); // Move to questions step
        } catch (error) {
            console.error('Error:', error);
            toast.error("Failed to generate questions.");
            setIsLoading(false);
        }
    };

    const handleNextStep = () => {
        if (currentStep === 1) {
            setCurrentStep(2);
        } else if (currentStep === 2) {
            fetchAndSetQuestions();
        } else {
            setCurrentStep(prev => prev + 1);
        }
    };

    const handlePrevStep = () => setCurrentStep(prev => prev - 1);

    // Question manipulation handlers
    const handleEdit = (id) => setQuestions(p => p.map(q => q.id === id ? { ...q, isEditing: !q.isEditing } : q));
    const handleDelete = (id) => setQuestions(p => p.filter(q => q.id !== id));
    const handleAddQuestion = () => setQuestions(p => [...p, { id: Math.random(), question: '', options: { a: '', b: '', c: '', d: '' }, answer: '', isEditing: true }]);
    const handleQuestionChange = (id, field, value, optKey) => setQuestions(p => p.map(q => q.id === id ? (field === 'options' ? { ...q, options: { ...q.options, [optKey]: value } } : { ...q, [field]: value }) : q));
    const handleAnswerChange = (id, answer) => setQuestions(p => p.map(q => q.id === id ? { ...q, answer } : q));
    const handleClearQuestions = () => {
        if (window.confirm("Are you sure you want to clear all the questions?")) {
            setQuestions([]);
        }
    };

    const handleFileUpload = async (event) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        if (!hasAgreedToPrivacy) {
            setPendingUploadEvent(Array.from(files));
            setShowPrivacyNotice(true);
            event.target.value = '';
            return;
        }

        uploadFilesToServer(Array.from(files));
        event.target.value = '';
    };

    const uploadFilesToServer = async (files) => {
        setIsUploading(true);
        setUploadProgress(0);
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.size > 16 * 1024 * 1024) { // 16MB limit
                toast.error(`File ${file.name} is too large (max 16MB).`);
                setIsUploading(false);
                return;
            }
            // Accept images, pdf, pptx (validated server-side too)
            formData.append(`file_${i}`, file);
        try {
            const response = await api.uploadFiles(formData, setUploadProgress);

            // New response format with metadata
            if (response?.items?.length > 0) {
                // Fetch preview blobs (if any)
                const built = await Promise.all(response.items.map(async (item) => {
                    const type = item.type;
                    let previewUrl = null;

                    if (item.previews && item.previews.length > 0) {
                        // Use server-generated preview
                        try {
                            const r = await api.getUploadedImage(item.previews[0]);
                            const b = await r.blob();
                            previewUrl = URL.createObjectURL(b);
                        } catch {
                            previewUrl = null;
                        }
                    } else if (type === 'image') {
                        // Fallback: fetch original image and create blob URL
                        try {
                            const r = await api.getUploadedImage(item.filename);
                            const b = await r.blob();
                            previewUrl = URL.createObjectURL(b);
                        } catch {
                            previewUrl = null;
                        }
                    }

                    return {
                        filename: item.filename,
                        type,
                        previewUrl,
                        url: previewUrl, // fallback key used by renderer
                        original: item.filename,
                        previews: item.previews || []
                    };
                }));
                setUploadedFiles(prev => [...prev, ...built]);
                toast.success('Files uploaded successfully!');
            } else if (response?.files?.length > 0) {
                // Legacy response format: only filenames (assume images)
                const builtLegacy = await Promise.all(response.files.map(async (filename) => {
                    let previewUrl = null;
                    try {
                        const r = await api.getUploadedImage(filename);
                        const b = await r.blob();
                        previewUrl = URL.createObjectURL(b);
                    } catch {
                        previewUrl = null;
                    }
                    return {
                        filename,
                        type: 'image',
                        previewUrl,
                        url: previewUrl,
                        original: filename,
                        previews: []
                    };
                }));
                setUploadedFiles(prev => [...prev, ...builtLegacy]);
                toast.success('Files uploaded successfully!');
            } else {
                toast.error('No files returned from server.');
            }
        } catch (error) {
            toast.error(error.message || 'Failed to upload files.');
        } finally {
            setIsUploading(false);
        }
            setIsUploading(false);
        }
    };

    const handleDeleteFile = (filename) => {
        setUploadedFiles(prev => prev.filter(f => f.filename !== filename));
    };

    const handleGenerateQuestions = async () => {
        if (uploadedFiles.length === 0) {
            toast.error('Please upload at least one file.');
            return;
        }

        setIsGenerating(true);
        setGenerationProgress({ completed: 0, total: 0, message: 'Initiating generation...' });
        setLoadingMessages(["Analyzing files..."]);

        let messageIndex = 0;
        const FAKE_MESSAGES = [
            "Analyzing files...",
            "Detecting question patterns...",
            "Optimizing OCR processing...",
            "Verifying answer consistency...",
            "Cross-referencing curriculum...",
            "Generating distractors..."
        ];

        const messageInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % FAKE_MESSAGES.length;
            setLoadingMessages([FAKE_MESSAGES[messageIndex]]);
        }, 3000);

        const filenames = uploadedFiles.map(f => f.original || f.filename);

        try {
            const generatedQuestions = await api.generateFromFiles(filenames, {
                onProgress: (progress) => {
                    setGenerationProgress(prev => ({ ...prev, ...progress }));
                },
                onMessage: (message) => {
                    setGenerationProgress(prev => ({ ...prev, message }));
                },
            });

            if (generatedQuestions && generatedQuestions.length > 0) {
                const formattedQuestions = generatedQuestions.map(q => ({ ...q, id: Math.random() }));
                setQuestions(prev => [...prev, ...formattedQuestions]);
                setNewQuestionIds(new Set(formattedQuestions.map(q => q.id)));
                toast.success(`${generatedQuestions.length} questions generated successfully!`);
            } else {
                setShowNoQuestionsDialog(true);
            }
        } catch (error) {
            if (error.message === 'No questions could be extracted from the files') {
                setShowNoQuestionsDialog(true);
            } else {
                toast.error(error.message || 'Failed to generate questions.');
            }
        } finally {
            clearInterval(messageInterval);
            setIsGenerating(false);
        }
    };

    const handleAgreeToPrivacy = () => {
        setHasAgreedToPrivacy(true);
        setShowPrivacyNotice(false);
        if (pendingUploadEvent) {
            uploadFilesToServer(pendingUploadEvent);
            setPendingUploadEvent(null);
        }
    };

    const handleFileClick = (file) => {
        const cachedUrl = file.previewUrl || file.url;
        if (cachedUrl) {
            setSelectedImage({ url: cachedUrl });
            return;
        }
        toast.error('Preview not available. Please re-upload the file.');
    };

    const handleClosePopup = () => {
        setSelectedImage(null);
    };
    
    const handleCloseNoQuestionsDialog = () => {
        setShowNoQuestionsDialog(false);
    };

    const renderLatexText = (text) => {
        if (!text) return null;
        const parts = text.split(/(\$[^\$]+\$)/g);
        return parts.map((part, index) =>
            part.startsWith('$') && part.endsWith('$') ?
            <InlineMath key={index} math={part.slice(1, -1)} /> : part
        );
    };

    const handleConfirmCreate = async () => {
        setOpenConfirm(false);
        setIsLoading(true);

        let testPayload = {
            subject: testDetails.subject,
            lessons: testDetails.lessons,
            test_name: testDetails.test_name,
            questions: questions.map(({ isEditing, ...q }) => q),
            class10: testDetails.class10,
        };

        if (!expirationDate) {
            toast.error("Please set an expiration date.");
            setIsLoading(false);
            return;
        }
        testPayload.expiration_date = expirationDate.toISOString();

        if (assignment.type === 'division') testPayload.division = assignment.division;
        else if (assignment.type === 'students') testPayload.students = assignment.students.map(s => s.id);
        
        try {
            await api.createTest(testPayload);
            toast.success("Test created successfully!");
            navigate('/history');
        } catch (error) {
            console.error('Error creating test:', error);
            toast.error('Failed to create test. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const STEPS_AUTOMATIC = ['Confirm Details', 'Assign Students', 'Review Questions', 'Set Expiration', 'Finalize'];

    return (
        <div className="create-test-page">
            <div className="create-test-container">
                <div className="create-test-header">
                    <h1>Automatic Test Creation</h1>
                    <Stepper currentStep={currentStep} steps={STEPS_AUTOMATIC} />
                </div>

                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                        transition={{ duration: 0.3 }}
                    >
                        {/* Automatic Mode Steps */}
                        {currentStep === 1 && (
                             <div className="step-card">
                                <h2>Step 1: Confirm Details</h2>
                                <div className="info-box">
                                    <FaInfoCircle />
                                    <p>The following details were selected for automatic question generation. Please confirm to proceed.</p>
                                </div>
                                <div className="details-grid">
                                    {testDetails.test_name && (
                                        <div className="detail-item">
                                            <p>Test Name</p>
                                            <span>{testDetails.test_name}</span>
                                        </div>
                                    )}
                                    <div className="detail-item">
                                        <p>Subject</p>
                                        <span>{testDetails.subject}</span>
                                    </div>
                                    <div className="detail-item">
                                        <p>Standard</p>
                                        <span>{testDetails.class10 ? '10th' : '9th'}</span>
                                    </div>
                                    <div className="detail-item full-width">
                                        <p>Lessons</p>
                                        <span>{Array.isArray(testDetails.lessons) ? testDetails.lessons.join(', ') : ''}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {currentStep === 2 && (
                           <div className="step-card">
                                <h2>Step 2: Assign Test</h2>
                                <div className="assignment-description">
                                    <p><strong>All Students:</strong> The test will be assigned to every student in the selected standard.</p>
                                    <p><strong>By Division:</strong> The test will be assigned to all students in a specific division (e.g., A, B, C).</p>
                                    <p><strong>Specific Students:</strong> The test will be assigned only to the individual students you select.</p>
                                </div>
                                <div className="assignment-options">
                                    <label><input type="radio" value="all" checked={assignment.type === 'all'} onChange={() => setAssignment(a => ({...a, type: 'all'}))} /> All Students</label>
                                    <label><input type="radio" value="division" checked={assignment.type === 'division'} onChange={() => setAssignment(a => ({...a, type: 'division'}))} /> By Division</label>
                                    <label><input type="radio" value="students" checked={assignment.type === 'students'} onChange={() => setAssignment(a => ({...a, type: 'students'}))} /> Specific Students</label>
                                </div>
                                {assignment.type === 'division' && (<select className="form-control" value={assignment.division} onChange={e => setAssignment(a => ({...a, division: e.target.value}))}><option value="">Select Division</option><option value="A">A</option><option value="B">B</option><option value="C">C</option></select>)}
                                {assignment.type === 'students' && (<div className="student-selector"><input type="text" placeholder="Search..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="form-control" /><div className="student-list">{allStudents.filter(s => s.name.toLowerCase().includes(searchTerm.toLowerCase())).map(s => (<div key={s.id} className="student-item" onClick={() => {!assignment.students.find(ss => ss.id === s.id) && setAssignment(a => ({...a, students: [...a.students, s]})); setSearchTerm('');}}>{s.name}</div>))}</div><div className="selected-students">{assignment.students.map(s => (<div key={s.id} className="selected-student-tag">{s.name}<button onClick={() => setAssignment(a => ({...a, students: a.students.filter(ss => ss.id !== s.id)}))}>&times;</button></div>))}</div></div>)}
                            </div>
                        )}

                        {currentStep === 3 && (
                            <>
                                <div className="step-card">
                                    <h2>Step 3: Review & Edit Questions</h2>
                                    {isLoading ? <p>Generating questions...</p> : <p>Here are the generated questions. You can edit, delete, or add more from images.</p>}
                                    <FileUploadSection
                                        uploadedFiles={uploadedFiles}
                                        isUploading={isUploading}
                                        uploadProgress={uploadProgress}
                                        isGenerating={isGenerating}
                                        generationProgress={generationProgress}
                                        loadingMessages={loadingMessages}
                                        handleFileUpload={handleFileUpload}
                                        handleDeleteFile={handleDeleteFile}
                                        handleGenerateQuestions={handleGenerateQuestions}
                                        handleFileClick={handleFileClick}
                                    />
                                </div>
                                <div className="question-list-container">
                                    <div className="buttons-container" style={{ justifyContent: 'flex-start', marginBottom: '1rem' }}>
                                        <button onClick={handleAddQuestion} className="btn-secondary"><FaPlus /> Add Question</button>
                                        {questions.length > 0 &&
                                            <button onClick={handleClearQuestions} className="btn-secondary btn-danger">
                                                <FaTrash /> Clear All
                                            </button>
                                        }
                                    </div>
                                    <AnimatePresence>
                                    {questions.map((q, i) => {
                                       const cardClasses = [
                                           'question-card',
                                           newQuestionIds.has(q.id) ? 'new-question' : '',
                                           !q.answer ? 'unanswered' : ''
                                       ].filter(Boolean).join(' ');
    
                                       return (
                                       <motion.div key={q.id} layout className={cardClasses}>
                                           <div className="question-number">{i + 1}</div>
                                           <div className="question-actions">
                                               <button onClick={() => handleEdit(q.id)} className="action-btn edit-btn"><FaEdit /></button>
                                               <button onClick={() => handleDelete(q.id)} className="action-btn delete-btn"><FaTrash /></button>
                                           </div>
                                           <div className="question-content">
                                               {q.isEditing ? (
                                                   <>
                                                       <textarea value={q.question} onChange={e => handleQuestionChange(q.id, 'question', e.target.value)} className="form-control" placeholder="Type question..."/>
                                                       <div className="options-grid">
                                                           {Object.keys(q.options).map(key => (
                                                               <input key={key} type="text" value={q.options[key]} onChange={e => handleQuestionChange(q.id, 'options', e.target.value, key)} className="form-control" placeholder={`Option ${key.toUpperCase()}`} />
                                                           ))}
                                                       </div>
                                                       <select value={q.answer} onChange={e => handleAnswerChange(q.id, e.target.value)} className="form-control answer-select">
                                                           <option value="">Select Answer</option>
                                                           {Object.keys(q.options).map(key => <option key={key} value={key}>{key.toUpperCase()}</option>)}
                                                       </select>
                                                   </>
                                               ) : (
                                                  <>
                                                      <div className="question-text">{renderLatexText(q.question)}</div>
                                                      <div className="options-grid view">
                                                          {Object.keys(q.options).map(key => (
                                                              <div key={key} className={`option ${q.answer === key ? 'selected' : ''}`} onClick={() => handleAnswerChange(q.id, key)}>
                                                                  <span>{key.toUpperCase()}.</span> {renderLatexText(q.options[key])}
                                                              </div>
                                                          ))}
                                                      </div>
                                                  </>
                                              )}
                                           </div>
                                       </motion.div>
                                       )
                                    })}
                                    </AnimatePresence>
                                </div>
                            </>
                        )}

                        {currentStep === 4 && (
                            <div className="step-card">
                                <h2>Step 4: Set Expiration</h2>
                                <p>Set an expiration date for this test. After this date, students will no longer be able to take it.</p>
                                <div className="date-picker-container">
                                    <div className="date-picker-input-container">
                                        <FaCalendarAlt className="date-picker-icon" />
                                        <DatePicker
                                            selected={expirationDate}
                                            onChange={(date) => setExpirationDate(date)}
                                            minDate={new Date()}
                                            placeholderText="Click to select a date"
                                            className="form-control"
                                            dateFormat="MMMM d, yyyy"
                                        />
                                    </div>
                                    {expirationDate && (
                                        <button className="clear-date-btn" onClick={() => setExpirationDate(null)}>
                                            &times;
                                        </button>
                                    )}
                                </div>
                                {expirationDate && (
                                    <div className="date-info">
                                        <p>Test will expire in <strong>{differenceInDays(expirationDate, new Date())}</strong> days.</p>
                                        <p>On <strong>{format(expirationDate, 'eeee, MMMM do, yyyy')}</strong>.</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {currentStep === 5 && (
                             <div className="step-card">
                                <h2>Step 5: Finalize & Create</h2>
                                <div className="summary-card">
                                    <h3>Test Summary</h3>
                                    {testDetails.test_name && <p><strong>Test Name:</strong> {testDetails.test_name}</p>}
                                    <p><strong>Subject:</strong> {testDetails.subject}</p>
                                    <p><strong>Lessons:</strong> {testDetails.lessons.join(', ')}</p>
                                    <p><strong>Questions:</strong> {questions.length} total</p>
                                    <p><strong>Assigned To:</strong> {assignment.type === 'all' ? 'All Students' : assignment.type === 'division' ? `Division ${assignment.division}` : `${assignment.students.length} specific students`}</p>
                                     {expirationDate && <p><strong>Expires On:</strong> {format(expirationDate, 'MMMM d, yyyy')}</p>}
                                </div>
                                <button onClick={() => setOpenConfirm(true)} className="btn-primary finalize-btn" disabled={isLoading}>
                                    {isLoading ? 'Creating...' : 'Confirm & Create Test'}
                                </button>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
                
                <div className="navigation-buttons">
                    {currentStep > 1 && <button onClick={handlePrevStep} className="btn-secondary"><FaArrowLeft /> Back</button>}
                    {currentStep < STEPS_AUTOMATIC.length && (
                        <button onClick={handleNextStep} className="btn-primary" disabled={isLoading}>
                           {isLoading ? 'Loading...' : 'Next'} <FaArrowRight />
                        </button>
                    )}
                </div>

                {openConfirm && (
                    <div className="dialog-overlay">
                        <motion.div className="dialog-content" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}>
                            <h3>Confirm Test Creation</h3>
                            <p>Are you sure you want to finalize and create this test?</p>
                            <div className="dialog-buttons">
                                <button onClick={() => setOpenConfirm(false)} className="btn-secondary">Cancel</button>
                                <button onClick={handleConfirmCreate} className="btn-primary">Confirm</button>
                            </div>
                        </motion.div>
                    </div>
                )}

                <Dialog open={showPrivacyNotice} onClose={() => setShowPrivacyNotice(false)} PaperProps={{ className: 'privacy-dialog-paper' }}>
                    <div className="dialog-content privacy-dialog">
                        <h3>🔒 Privacy Notice</h3>
                        <div className="privacy-text">
                            <p>Before proceeding, please carefully read and acknowledge the following privacy terms:</p>
                            <p>1. Any images you upload will be stored on AcePlus servers located in Romania.</p>
                            <p>2. Do not upload any images containing sensitive, private, or confidential information that you wish to keep private.</p>
                            <p>3. The creator, Ayush Pandey, maintains complete rights and authority to access, test, check, and verify any uploaded images for the purpose of product improvement and quality assurance.</p>
                            <p>4. By clicking "I Agree", you acknowledge that you understand and accept these terms regarding the handling and storage of your uploaded images.</p>
                        </div>
                        <div className="dialog-buttons">
                             <button onClick={() => setShowPrivacyNotice(false)} className="btn-secondary">Cancel</button>
                             <button onClick={handleAgreeToPrivacy} className="btn-primary agree-btn">I Agree</button>
                        </div>
                    </div>
                </Dialog>
                
                <Dialog open={showNoQuestionsDialog} onClose={handleCloseNoQuestionsDialog} PaperProps={{className: 'no-questions-dialog-paper'}}>
                     <div className="dialog-content no-questions-dialog">
                         <div className="dialog-icon">⚠️</div>
                         <h3>No Questions Detected</h3>
                         <p>We couldn't detect any questions from the uploaded images.</p>
                         <div className="possible-reasons">
                             <h4>This might be because:</h4>
                             <ul>
                                 <li>The image doesn't contain any questions</li>
                                 <li>The image quality is too low or unclear</li>
                                 <li>The text in the image is not properly visible</li>
                                 <li>The questions are not in a recognizable format</li>
                             </ul>
                         </div>
                         <p>Please check your images and try again with clear, well-lit photos of questions.</p>
                         <div className="dialog-buttons">
                             <button onClick={handleCloseNoQuestionsDialog} className="btn-primary">I Understand</button>
                         </div>
                     </div>
                </Dialog>

                <AnimatePresence>
                {selectedImage && (
                    <motion.div className="image-popup-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={handleClosePopup}>
                        <motion.div className="image-popup-content" initial={{ scale: 0.8 }} animate={{ scale: 1 }} exit={{ scale: 0.8 }} onClick={(e) => e.stopPropagation()}>
                            <img src={selectedImage.url} alt="Selected preview" />
                            <button className="close-popup-btn" onClick={handleClosePopup}>&times;</button>
                        </motion.div>
                    </motion.div>
                )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default CreateTest;