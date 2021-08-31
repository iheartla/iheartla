var Module=typeof pyodide._module!=="undefined"?pyodide._module:{};if(!Module.expectedDataFileDownloads){Module.expectedDataFileDownloads=0}Module.expectedDataFileDownloads++;(function(){var loadPackage=function(metadata){var PACKAGE_PATH;if(typeof window==="object"){PACKAGE_PATH=window["encodeURIComponent"](window.location.pathname.toString().substring(0,window.location.pathname.toString().lastIndexOf("/"))+"/")}else if(typeof location!=="undefined"){PACKAGE_PATH=encodeURIComponent(location.pathname.toString().substring(0,location.pathname.toString().lastIndexOf("/"))+"/")}else{throw"using preloaded data can only be done on a web page or in a web worker"}var PACKAGE_NAME="nlopt.data";var REMOTE_PACKAGE_BASE="nlopt.data";if(typeof Module["locateFilePackage"]==="function"&&!Module["locateFile"]){Module["locateFile"]=Module["locateFilePackage"];err("warning: you defined Module.locateFilePackage, that has been renamed to Module.locateFile (using your locateFilePackage for now)")}var REMOTE_PACKAGE_NAME=Module["locateFile"]?Module["locateFile"](REMOTE_PACKAGE_BASE,""):REMOTE_PACKAGE_BASE;var REMOTE_PACKAGE_SIZE=metadata["remote_package_size"];var PACKAGE_UUID=metadata["package_uuid"];function fetchRemotePackage(packageName,packageSize,callback,errback){var xhr=new XMLHttpRequest;xhr.open("GET",packageName,true);xhr.responseType="arraybuffer";xhr.onprogress=function(event){var url=packageName;var size=packageSize;if(event.total)size=event.total;if(event.loaded){if(!xhr.addedTotal){xhr.addedTotal=true;if(!Module.dataFileDownloads)Module.dataFileDownloads={};Module.dataFileDownloads[url]={loaded:event.loaded,total:size}}else{Module.dataFileDownloads[url].loaded=event.loaded}var total=0;var loaded=0;var num=0;for(var download in Module.dataFileDownloads){var data=Module.dataFileDownloads[download];total+=data.total;loaded+=data.loaded;num++}total=Math.ceil(total*Module.expectedDataFileDownloads/num);if(Module["setStatus"])Module["setStatus"]("Downloading data... ("+loaded+"/"+total+")")}else if(!Module.dataFileDownloads){if(Module["setStatus"])Module["setStatus"]("Downloading data...")}};xhr.onerror=function(event){throw new Error("NetworkError for: "+packageName)};xhr.onload=function(event){if(xhr.status==200||xhr.status==304||xhr.status==206||xhr.status==0&&xhr.response){var packageData=xhr.response;callback(packageData)}else{throw new Error(xhr.statusText+" : "+xhr.responseURL)}};xhr.send(null)}function handleError(error){console.error("package error:",error)}var fetchedCallback=null;var fetched=Module["getPreloadedPackage"]?Module["getPreloadedPackage"](REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE):null;if(!fetched)fetchRemotePackage(REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE,function(data){if(fetchedCallback){fetchedCallback(data);fetchedCallback=null}else{fetched=data}},handleError);function runWithFS(){function assert(check,msg){if(!check)throw msg+(new Error).stack}Module["FS_createPath"]("/","lib",true,true);Module["FS_createPath"]("/lib","python3.8",true,true);Module["FS_createPath"]("/lib/python3.8","site-packages",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","nlopt",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","nlopt-2.7.0-py3.8.egg-info",true,true);function processPackageData(arrayBuffer){assert(arrayBuffer,"Loading data file failed.");assert(arrayBuffer instanceof ArrayBuffer,"bad input to processPackageData");var byteArray=new Uint8Array(arrayBuffer);var curr;var compressedData={data:null,cachedOffset:365599,cachedIndexes:[-1,-1],cachedChunks:[null,null],offsets:[0,1284,2286,2920,3474,4423,5134,5757,6304,7153,8329,9611,10784,11779,13019,14227,15404,16534,17883,19221,20434,21546,22840,23729,24581,25186,25865,26505,27122,27740,28475,29493,30620,31737,32852,33930,34970,36073,37224,38368,39593,40726,41809,42906,44042,45093,46530,47497,48598,49860,51099,52214,53466,54970,56619,58068,59608,61020,62299,63956,65306,66690,67859,69169,70468,71916,73346,74765,76134,77676,79189,80715,82057,83634,84919,86337,87398,88608,90230,91712,93153,94551,95900,97399,98826,100277,101705,102932,104282,105766,107075,108499,110004,111307,112799,113961,115308,116887,118336,119866,121430,122762,124238,125615,127021,128366,129863,131345,132724,133781,134886,136146,137520,138844,140302,141838,143218,144595,146165,147587,148994,150530,151872,153212,154665,155957,157526,159025,160522,161901,163237,164427,165716,167184,168313,169809,171205,172696,174185,175509,176994,178394,179624,181016,182034,183067,183763,184606,185768,186919,187891,189080,190388,191520,192766,193876,195085,196232,197669,198649,199938,201019,202039,202730,203170,204077,205306,206557,207768,208518,209825,210790,211881,212995,214133,215402,216867,218385,219641,220912,222244,223389,223929,224880,226131,227237,228645,229831,231020,231583,232386,233059,233437,233809,234703,235767,236675,237394,238166,239716,240538,241136,242404,243158,243675,244228,244927,245908,247059,248663,249975,251416,252714,253764,254756,256227,257659,259015,260582,261653,262995,264240,265398,266611,267723,268998,270178,271245,272441,273419,274620,275632,276880,278132,279418,280666,281975,283274,284004,285168,286545,287830,288615,289541,290763,291806,293142,294528,296208,297564,298379,299182,300052,301033,301817,302755,303986,305226,305389,305672,305939,306298,306612,307495,309350,311398,312427,312455,312730,313540,314402,315519,316652,318013,319401,320829,322256,323685,325176,326614,328138,329556,331067,332477,334043,335579,336968,338646,339923,341733,342418,344353,345357,346498,348411,349556,350576,351671,352218,352772,353424,353965,354539,355083,355538,356320,357013,357525,358049,358660,359264,359827,360517,361494,362827,363892,364667,364731,365071],sizes:[1284,1002,634,554,949,711,623,547,849,1176,1282,1173,995,1240,1208,1177,1130,1349,1338,1213,1112,1294,889,852,605,679,640,617,618,735,1018,1127,1117,1115,1078,1040,1103,1151,1144,1225,1133,1083,1097,1136,1051,1437,967,1101,1262,1239,1115,1252,1504,1649,1449,1540,1412,1279,1657,1350,1384,1169,1310,1299,1448,1430,1419,1369,1542,1513,1526,1342,1577,1285,1418,1061,1210,1622,1482,1441,1398,1349,1499,1427,1451,1428,1227,1350,1484,1309,1424,1505,1303,1492,1162,1347,1579,1449,1530,1564,1332,1476,1377,1406,1345,1497,1482,1379,1057,1105,1260,1374,1324,1458,1536,1380,1377,1570,1422,1407,1536,1342,1340,1453,1292,1569,1499,1497,1379,1336,1190,1289,1468,1129,1496,1396,1491,1489,1324,1485,1400,1230,1392,1018,1033,696,843,1162,1151,972,1189,1308,1132,1246,1110,1209,1147,1437,980,1289,1081,1020,691,440,907,1229,1251,1211,750,1307,965,1091,1114,1138,1269,1465,1518,1256,1271,1332,1145,540,951,1251,1106,1408,1186,1189,563,803,673,378,372,894,1064,908,719,772,1550,822,598,1268,754,517,553,699,981,1151,1604,1312,1441,1298,1050,992,1471,1432,1356,1567,1071,1342,1245,1158,1213,1112,1275,1180,1067,1196,978,1201,1012,1248,1252,1286,1248,1309,1299,730,1164,1377,1285,785,926,1222,1043,1336,1386,1680,1356,815,803,870,981,784,938,1231,1240,163,283,267,359,314,883,1855,2048,1029,28,275,810,862,1117,1133,1361,1388,1428,1427,1429,1491,1438,1524,1418,1511,1410,1566,1536,1389,1678,1277,1810,685,1935,1004,1141,1913,1145,1020,1095,547,554,652,541,574,544,455,782,693,512,524,611,604,563,690,977,1333,1065,775,64,340,528],successes:[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]};compressedData["data"]=byteArray;assert(typeof Module.LZ4==="object","LZ4 not present - was your app build with  -s LZ4=1  ?");Module.LZ4.loadPackage({metadata:metadata,compressedData:compressedData},true);Module["removeRunDependency"]("datafile_nlopt.data")}Module["addRunDependency"]("datafile_nlopt.data");if(!Module.preloadResults)Module.preloadResults={};Module.preloadResults[PACKAGE_NAME]={fromCache:false};if(fetched){processPackageData(fetched);fetched=null}else{fetchedCallback=processPackageData}}if(Module["calledRun"]){runWithFS()}else{if(!Module["preRun"])Module["preRun"]=[];Module["preRun"].push(runWithFS)}};loadPackage({files:[{filename:"/lib/python3.8/site-packages/nlopt/__init__.py",start:0,end:44,audio:0},{filename:"/lib/python3.8/site-packages/nlopt/nlopt.py",start:44,end:17987,audio:0},{filename:"/lib/python3.8/site-packages/nlopt/_nlopt.so",start:17987,end:650768,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/PKG-INFO",start:650768,end:650947,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/not-zip-safe",start:650947,end:650948,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/dependency_links.txt",start:650948,end:650949,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/requires.txt",start:650949,end:650961,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/top_level.txt",start:650961,end:650967,audio:0},{filename:"/lib/python3.8/site-packages/nlopt-2.7.0-py3.8.egg-info/SOURCES.txt",start:650967,end:652276,audio:0}],remote_package_size:369695,package_uuid:"ed35a9d1-0440-4dfa-b12e-17f47cc83a68"})})();