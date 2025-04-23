import React, { useEffect, useState, useRef, useCallback } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../utils/api';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: ${props => props.$isActive ? 1000 : 999};
  pointer-events: ${props => props.$isActive ? 'all' : 'none'};
`;

const PopupContent = styled(motion.div)`
  background: rgba(26, 26, 26, 0.95);
  padding: 2rem;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  min-height: 500px;
  overflow-y: auto;
  position: relative;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  filter: ${props => props.$isActive ? 'none' : 'blur(3px) brightness(0.7)'};
  transition: filter 0.3s;
  
  @media (max-width: 768px) {
    padding: 1.5rem;
    width: 95%;
  }
  
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #222;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 4px;
    
    &:hover {
      background: #555;
    }
  }
`;

const Header = styled(motion.h2)`
  text-align: center;
  margin-bottom: 1rem;
  color: #fff;
  font-size: 1.8rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  
  @media (max-width: 768px) {
    font-size: 1.5rem;
    margin-bottom: 0.8rem;
  }
  
  @media (max-width: 480px) {
    font-size: 1.3rem;
    margin-bottom: 0.6rem;
  }
`;

const SubHeader = styled(motion.div)`
  text-align: center;
  margin-bottom: 1.5rem;
  color: #999;
  font-size: 0.9rem;
  
  @media (max-width: 768px) {
    font-size: 0.8rem;
    margin-bottom: 1.2rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.75rem;
    margin-bottom: 1rem;
  }
`;

const TableContainer = styled.div`
  width: 100%;
  overflow-x: hidden;
  margin-top: 1rem;
  
  @media (max-width: 768px) {
    margin-top: 0.8rem;
  }
  
  @media (max-width: 480px) {
    margin-top: 0.6rem;
  }
`;

const Table = styled(motion.table)`
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin: 0;
  padding: 0;
  border: none;
`;

const Th = styled.th`
  padding: 0.75rem 0.5rem;
  text-align: left;
  border-bottom: 2px solid #333;
  color: #fff;
  font-weight: 600;
  white-space: normal;
  word-wrap: break-word;
  width: ${props => props.width || 'auto'};
  font-size: 0.95rem;
  line-height: 1.2;
  
  &:last-child {
    padding-right: 0;
  }
  
  @media (max-width: 768px) {
    padding: 0.5rem 0.3rem;
    font-size: 0.8rem;
  }
  
  @media (max-width: 600px) {
    padding: 0.4rem 0.25rem;
    font-size: 0.7rem;
  }
  
  @media (max-width: 480px) {
    padding: 0.3rem 0.2rem;
    font-size: 0.65rem;
  }
  
  @media (max-width: 400px) {
    padding: 0.25rem 0.15rem;
    font-size: 0.6rem;
  }
`;

const Td = styled.td`
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid #333;
  color: #ccc;
  white-space: normal;
  word-wrap: break-word;
  font-size: 1rem;
  
  &:last-child {
    padding-right: 0;
  }
  
  @media (max-width: 768px) {
    padding: 0.5rem 0.3rem;
    font-size: 0.9rem;
  }
  
  @media (max-width: 480px) {
    padding: 0.4rem 0.2rem;
    font-size: 0.8rem;
  }
`;

const MedalRow = styled(motion.tr)`
  background: ${props => {
    if (props.noExams) return 'rgba(255, 0, 0, 0.1)';
    if (props.rank === 1) return 'linear-gradient(to right, rgba(255, 215, 0, 0.15), transparent)';
    if (props.rank === 2) return 'linear-gradient(to right, rgba(192, 192, 192, 0.15), transparent)';
    if (props.rank === 3) return 'linear-gradient(to right, rgba(205, 127, 50, 0.15), transparent)';
    return 'transparent';
  }};
  transition: background-color 0.3s;

  &:hover {
    background: ${props => {
      if (props.noExams) return 'rgba(255, 0, 0, 0.15)';
      if (props.rank === 1) return 'linear-gradient(to right, rgba(255, 215, 0, 0.2), transparent)';
      if (props.rank === 2) return 'linear-gradient(to right, rgba(192, 192, 192, 0.2), transparent)';
      if (props.rank === 3) return 'linear-gradient(to right, rgba(205, 127, 50, 0.2), transparent)';
      return '#222';
    }};
  }
`;

const Medal = styled(motion.span)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  width: 32px;
  height: 32px;
  text-align: center;
  
  @media (max-width: 768px) {
    font-size: 1rem;
    width: 28px;
    height: 28px;
  }
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
    width: 24px;
    height: 24px;
  }
`;

const RankNumber = styled(Medal)`
  font-size: 1rem;
  color: #666;
  
  @media (max-width: 768px) {
    font-size: 0.9rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
  }
`;

const Score = styled(motion.span)`
  display: inline-block;
  color: ${props => {
    if (props.value >= 90) return '#4CAF50';
    if (props.value >= 70) return '#8BC34A';
    if (props.value >= 50) return '#FFC107';
    return '#ccc';
  }};
  font-size: 1rem;
  
  @media (max-width: 768px) {
    font-size: 0.9rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
  }
`;

const CloseButton = styled.button`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  transition: color 0.3s;
  
  &:hover {
    color: #fff;
  }
`;

const NoDataMessage = styled(motion.div)`
  text-align: center;
  color: #999;
  padding: 2rem;
  font-style: italic;
  font-size: 1rem;
  
  @media (max-width: 768px) {
    font-size: 0.9rem;
    padding: 1.5rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
    padding: 1rem;
  }
`;

const ResetMessage = styled(motion.div)`
  color: #666;
  font-size: 0.8rem;
  margin-top: 0.5rem;
  font-style: italic;
  
  @media (max-width: 768px) {
    font-size: 0.75rem;
    margin-top: 0.4rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.7rem;
    margin-top: 0.3rem;
  }
`;

const NoExamsText = styled.span`
  color: #ff6b6b;
  font-style: italic;
  font-size: 0.85rem;
  font-weight: 300;
  margin-left: 8px;
  display: inline-block;
  
  @media (max-width: 768px) {
    font-size: 0.75rem;
    margin-left: 6px;
  }
  
  @media (max-width: 480px) {
    font-size: 0.7rem;
    margin-left: 4px;
  }
`;

const EloScore = styled(motion.span)`
  color: #4dabf7;
  font-weight: 500;
  font-size: 1rem;
  
  @media (max-width: 768px) {
    font-size: 0.9rem;
  }
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
  }
`;

const Spinner = styled(motion.div)`
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top: 3px solid #4dabf7;
  border-radius: 50%;
  margin: 0 auto;
`;

const LoadingIndicator = styled(motion.div)`
  text-align: center;
  padding: 1rem;
  color: #666;
  font-style: italic;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
`;

const LeaderboardPopup = ({ isOpen, onClose, leaderboardData, updatePopupOpen }) => {
  const [isClosing, setIsClosing] = useState(false);
  const [showContent, setShowContent] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [students, setStudents] = useState([]);
  const tableRef = useRef(null);
  const popupContentRef = useRef(null);
  const [month, setMonth] = useState('');
  const [division, setDivision] = useState('');
  const [isClass10, setIsClass10] = useState(false);

  useEffect(() => {
    if (!updatePopupOpen && isOpen) {
      const timer = setTimeout(() => {
        setShowContent(true);
        // Initialize with first page data
        if (leaderboardData) {
          setStudents(leaderboardData.leaderboard || []);
          setMonth(leaderboardData.month || '');
          setDivision(leaderboardData.division || '');
          setIsClass10(leaderboardData.class === '10');
          setHasMore(leaderboardData.pagination?.total_count > 20);
          setCurrentPage(1); // Reset page when popup opens
        }
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [updatePopupOpen, isOpen, leaderboardData]);

  const loadMoreData = useCallback(async () => {
    if (loading || !hasMore) return;

    try {
      setLoading(true);
      const nextPage = currentPage + 1;
      const response = await api.getLeaderboard(nextPage);

      if (response && response.leaderboard) {
        setStudents(prev => [...prev, ...response.leaderboard]);
        setCurrentPage(nextPage);
        setHasMore(response.pagination?.total_count > nextPage * 20);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      setError('Failed to load more students');
      console.error('Error loading more students:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, loading, hasMore]);

  useEffect(() => {
    const handleIntersection = (entries) => {
      if (entries[0].isIntersecting && hasMore && !loading) {
        loadMoreData();
      }
    };

    if (tableRef.current && popupContentRef.current && hasMore) {
      const observer = new IntersectionObserver(
        handleIntersection,
        {
          root: popupContentRef.current,
          threshold: 0.1
        }
      );

      // Get the last row to observe
      const rows = tableRef.current.querySelectorAll('tbody tr');
      if (rows.length > 0) {
        const lastRow = rows[rows.length - 1];
        observer.observe(lastRow);
      }

      return () => observer.disconnect();
    }
  }, [loading, hasMore, loadMoreData, students.length]);

  const handleClose = () => {
    setIsClosing(true);
    // Trigger card number animations
    window.dispatchEvent(new CustomEvent('animateCards'));
    setTimeout(() => {
      setShowContent(false);
      setTimeout(() => {
        setIsClosing(false);
        onClose();
      }, 200);
    }, 100);
  };

  if (!isOpen) return null;

  const getMedal = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return null;
  };

  const filteredLeaderboard = students.filter(entry => entry.name !== 'UNKNOWN')
    .map(entry => ({...entry
    }));

  const isActive = !updatePopupOpen;

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <PopupOverlay
          className="leaderboard-popup"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={handleClose}
          $isActive={isActive}
          ref={popupContentRef}
        >
          <PopupContent
            initial={{ scale: 0.95, y: 20, opacity: 0 }}
            animate={{ 
              scale: 1, 
              y: 0, 
              opacity: 1,
              transition: { duration: 0.5 }
            }}
            exit={{ 
              opacity: 0,
              transition: { duration: 0.2 }
            }}
            onClick={(e) => e.stopPropagation()}
            $isActive={isActive}
          >
            <CloseButton onClick={handleClose}>&times;</CloseButton>
            
            <AnimatePresence mode="wait">
              {showContent ? (
                <motion.div
                  key="content"
                  style={{ marginRight: "-20px", marginLeft: "-20px", marginBottom: "-30px" }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ 
                    opacity: 0,
                    transition: { duration: 0.2 }
                  }}
                >
                  <Header
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  >
                    Leaderboard
                  </Header>
                  <SubHeader
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                  >
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.4 }}
                    >
                      Division {division}
                    </motion.div>
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.5 }}
                    >
                      {month}
                    </motion.div>
                    <ResetMessage
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.6 }}
                    >
                      Leaderboard resets at the beginning of each month
                    </ResetMessage>
                  </SubHeader>

                  {students.length === 0 ? (
                    <NoDataMessage
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      No exams taken this month yet!
                    </NoDataMessage>
                  ) : (
                    <TableContainer ref={tableRef}>
                      <Table
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5, delay: 0.4 }}
                      >
                        <motion.thead
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.5 }}
                        >
                          <tr>
                            <Th width="12%">Rank</Th>
                            <Th width="38%">Name</Th>
                            <Th width="16%">Exams</Th>
                            <Th width="17%">Avg %</Th>
                            <Th width="17%">ELO</Th>
                          </tr>
                        </motion.thead>
                        <tbody>
                          {filteredLeaderboard.map((entry, index) => (
                            <MedalRow
                              key={entry.name}
                              rank={entry.rank}
                              noExams={entry.total_exams === 0}
                              initial={index < 20 ? { opacity: 0, x: -50 } : { opacity: 1, x: 0 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{
                                duration: index < 20 ? 0.3 : 0,
                                delay: index < 20 ? 0.6 + (index * 0.1) : 0
                              }}
                            >
                              <Td>
                                {getMedal(entry.rank) ? (
                                  <Medal
                                    initial={index < 20 ? { scale: 0, rotate: -180 } : { scale: 1, rotate: 0 }}
                                    animate={{ scale: 1, rotate: 0 }}
                                    transition={{
                                      type: "spring",
                                      stiffness: 200,
                                      damping: 15,
                                      delay: index < 20 ? 0.7 + (index * 0.1) : 0
                                    }}
                                  >
                                    {getMedal(entry.rank)}
                                  </Medal>
                                ) : (
                                  <RankNumber
                                    initial={index < 20 ? { scale: 0 } : { scale: 1 }}
                                    animate={{ scale: 1 }}
                                    transition={{
                                      type: "spring",
                                      stiffness: 200,
                                      damping: 15,
                                      delay: index < 20 ? 0.7 + (index * 0.1) : 0
                                    }}
                                  >
                                    {entry.rank}
                                  </RankNumber>
                                )}
                              </Td>
                              <Td>
                                {entry.name}
                                {entry.total_exams === 0 && (
                                  <NoExamsText>(No Exams Given Yet)</NoExamsText>
                                )}
                              </Td>
                              <Td>{entry.total_exams}</Td>
                              <Td>
                                <Score
                                  value={entry.average_percentage}
                                  initial={index < 20 ? { opacity: 0, scale: 0.5 } : { opacity: 1, scale: 1 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  transition={{
                                    type: "spring",
                                    stiffness: 200,
                                    damping: 10,
                                    delay: index < 20 ? 0.8 + (index * 0.1) : 0
                                  }}
                                >
                                  {entry.average_percentage}%
                                </Score>
                              </Td>
                              <Td>
                                <EloScore
                                  initial={index < 20 ? { opacity: 0, scale: 0.5 } : { opacity: 1, scale: 1 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  transition={{
                                    type: "spring",
                                    stiffness: 200,
                                    damping: 10,
                                    delay: index < 20 ? 0.8 + (index * 0.1) : 0
                                  }}
                                >
                                  {entry.elo_score || entry.eloScore || 'N/A'}
                                </EloScore>
                              </Td>
                            </MedalRow>
                          ))}
                        </tbody>
                        {(loading || hasMore) && (
                          <LoadingIndicator
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                           style={{
                              position: 'sticky',
                              bottom: 0,
                              backgroundColor: 'rgba(26, 26, 26, 0.95)'
                            }}
                           >
                            <Spinner
                              animate={{ rotate: 360 }}
                              transition={{
                                duration: 1,
                                repeat: Infinity,
                                ease: "linear"
                              }}
                            />
                            {loading ? 'Loading more students...' : 'Scroll for more'}
                          </LoadingIndicator>
                        )}
                        {error && <div>{error}</div>}
                      </Table>
                    </TableContainer>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="empty-state"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '500px'
                  }}
                >
                  <Header style={{ color: '#666' }}>Leaderboard</Header>
                </motion.div>
              )}
            </AnimatePresence>
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default LeaderboardPopup;