const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

// 'http://0.0.0.0:8080/profile/get_profile_lineChart?userName=amarkets_asia'

const endpoints = {
  // GET APIs

  //Dashboard
  getPieChart: `${API_BASE_URL}/dashboard/get_media_percentage`,
  getWordCloud: `${API_BASE_URL}/dashboard/get_word_cloud_data`,
  getWatchList: `${API_BASE_URL}/dashboard/get_watchlist_engagement_line_chart`,
  getStakedBarChart: `${API_BASE_URL}/dashboard/get_stakedBarChart`,
  getMediaPercents: `${API_BASE_URL}/dashboard/get_media_percentage`,
  getTrendLine: `${API_BASE_URL}/dashboard/get_trend_line_chart`,
  getScannedDetails: `${API_BASE_URL}/dashboard/get_dashboard_counts_with_percentage`,

  //Profile and Creator
  getProfileDO: `${API_BASE_URL}/profile/get_all_profile_similarity_data_observatory`,
  getCreatorHeatMap: `${API_BASE_URL}/profile/get_profile_heatmap`,
  getCreatorPosts: `${API_BASE_URL}/creator/get_creator_scams`,
  getCreatorProfile: `${API_BASE_URL}/creator/get_creator_statistics`,
  getCreatorLinechartData: `${API_BASE_URL}/profile/get_profile_lineChart`,

  //WatchList
  getCreatorRanking: `${API_BASE_URL}/watchlist/get_all_profile_rank_data`,
  getPostContents: `${API_BASE_URL}/watchlist/get_all_latest_content`,

  //Category and News List
  // getMindMap: `${API_BASE_URL}/category/get_all_category_mindmap_data?category=hate%20speech`,
  // getCategoryFilter: `${API_BASE_URL}/category/get_category_subCategoryflaged_count`,
  getMindMap: `${API_BASE_URL}/cross-category-insight/filter-category`,
  getNewsList: `${API_BASE_URL}/news`,
  visualChart: `${API_BASE_URL}/category/insights/visual-chart-data`,
  category: `${API_BASE_URL}/category`,
  getSearchCategories: `${API_BASE_URL}/cross-category-insight/search-categories`,
  getKeywordTrends: `${API_BASE_URL}/cross-category-insight/keyword-trends`,

  //Content
  getCategoryDO: `${API_BASE_URL}/content/get_data_observatory`,
  // getContentList: `${API_BASE_URL}/content/get_all_content_list`,
  
  getContentDetail: `${API_BASE_URL}/content/get_all_content_details`,
  getContentFilter: `${API_BASE_URL}/content/get_content_category_details`,
  getRankingWithFilter: `${API_BASE_URL}/content/get_all_profile_rank_data_with_filter`,
  getHashTags: `${API_BASE_URL}/content/get_all_hashtag_list`,
  getSimilarContents: `${API_BASE_URL}/report/get_content_by_video_id`,
  getTaskAndPercentage: `${API_BASE_URL}/content/get_percentage_high_low_medium`, // /content/get_percentage_high_low_medium?category=hate%20speech&subCategory=Forex&topic=Forex%20Investment

  getComments: `${API_BASE_URL}/comment/get_all_comments`,
  getCommentDetails: `${API_BASE_URL}/comment/get_comment_details?`,
  getLaws: `${API_BASE_URL}/regulations_laws/get_all_regulations_laws`,



  // Archive
  getReportedData: `${API_BASE_URL}/archive/get_all_reported_resolved_content_list`,

  // POST APIs
  postVideoContentReport: `${API_BASE_URL}/report/post_video_report/`,
  postProfileReport: `${API_BASE_URL}/report/post_profile_report/`,

  // authentication

  login: `${API_BASE_URL}/login_authentication_router/token`,
  // category insight

  getJustificationByName: `${API_BASE_URL}/category/get_justification_by_name?name=`,

  //agent
  getAgentList: `${API_BASE_URL}/agent/`,
  getContentList: `${API_BASE_URL}/content/all`,
  updateAgent: `${API_BASE_URL}/agent/`,
  postCrawlerPreviewAnalysis: `http://a341f22b8172041bda26bbd7862d3d68-1268475161.ap-southeast-1.elb.amazonaws.com:8001/yankechil_processor/filter_preproceed_data/`, // This POST API need to be fix after BE fix
  postCrawlerPreviewStep1: `${API_BASE_URL}/agent/`,

  //law violation
  getLawViolations: `${API_BASE_URL}/law_violation/law_violation_files`,
  getLawViolationDetail: `${API_BASE_URL}/law_violation/law_violation_file`,
  deleteLawViolationFile: `${API_BASE_URL}/law_violation/delete_file`,
  postLawViolationFile: `${API_BASE_URL}/law_violation/upload_file`,
  editLawViolationFile: `${API_BASE_URL}/law_violation/edit_file_details`,

  //direct link analysis
  postDirectLinkUrl: `${API_BASE_URL}/direct_link_analysis`,
  getDirectLinkTableData: `${API_BASE_URL}/direct_link_analysis/content-list`,
  getAgentContentList: `${API_BASE_URL}/direct_link_analysis/agent-content-list`
};

export default endpoints;

