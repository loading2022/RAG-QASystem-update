var folderList=document.querySelector(".folderList");
var fileListNav=document.querySelector(".fileList-nav");
var folder=document.querySelectorAll(".folder");

function updateList(folderName){
  var fileList=document.querySelector(".file-list");
  fetch('/getFiles', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ folderName: folderName }),
  })
    .then(response => response.json())
    .then(data => {
      fileList.innerHTML = ""; 
      if(data.files.length === 0){
        var li = document.createElement('li');
        li.innerHTML = `<p class="file">No file exists in this folder</p>`;
        fileList.appendChild(li);
      } else {
        data.files.forEach(filename => {
          var li = document.createElement('li');
          li.classList.add("file");
          li.innerHTML = `<p class="filename">${filename}</p><i class="fa-solid fa-trash" style="color: #051a66;" onclick="deleteItem('${filename}', '${folderName}')"></i>`;
          fileList.appendChild(li);
        });
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

function getCurrentDate() {
  var date = new Date();
  var year = date.getFullYear();
  var month = date.getMonth() + 1;
  var day = date.getDate();
  return year + '/' + (month < 10 ? '0' : '') + month + '/' + (day < 10 ? '0' : '') + day;
}
function deleteItem(filename, folderPath) {
  fetch('/deleteText', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ filename: filename, folderName: folderPath })
  })
  .then(response => {
      if (!response.ok) {
          throw new Error('Failed to delete file');
      }
      alert("Save!");
      return response.json();
  })
  .then(data => {
      updateList(folderPath);
  })
  .catch(error => {
      console.error('Error deleting file:', error);
      alert('Error deleting file');
  });
}


document.addEventListener("DOMContentLoaded", function() {
  fetch('/getFolders')
  .then(response => response.json())
  .then(data => {
    data.folders.forEach(folder => {
      var li = document.createElement('li');
      li.classList.add("folder");
      
      li.innerHTML = `
          <i class="fas fa-folder" style="color: #FFD43B;"></i>
          <p class="folderName">${folder.name}</p>
          <span class="folderUpdate">Last modified ${folder.time}</span>`;
      folderList.appendChild(li);
    });
  })
  .catch((error) => {
    console.error('Error:', error);
  });
});

var folderName = ''; 
folderList.addEventListener("click", function(e) {
  console.log("click");
  var fileList=document.querySelector(".file-list");
  fileList.innerHTML="";
  if (e.target && e.target.matches(".folder")) { 
    const folderItem = e.target.closest('.folder');
    folderName = folderItem.querySelector(".folderName").innerText;
    fileListNav.innerHTML=`<h2 class="file-title">${folderName}的文件列表</h2>
    <form enctype="multipart/form-data" action="/upload_file" method="post" accept-charset="UTF-8" id="upload-form">
            <label for="file-upload" class="upload-button"><i class="fas fa-file-upload"></i>上傳檔案</label>
            <input id="file-upload" type="file" name="filename" class="file-upload" multiple hidden/>
        </form>
    `;

    fetch('/getFiles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ folderName: folderName }),
    })
    .then(response=>response.json())
    .then(data=>{  
      if(data.files.length==0){
        var li = document.createElement('li');
        li.innerHTML = `<p class="filename">No file exists in this folder</p>`;
        fileList.appendChild(li);
      }   
      else{
        data.files.forEach(filename=>{
          var li = document.createElement('li');
          li.classList.add("file");
          li.innerHTML = `<p class="filename">${filename}</p><i class="fa-solid fa-trash" style="color: #051a66;" onclick="deleteItem('${filename}', '${folderName}')"></i>`;
          fileList.appendChild(li);
      }
      )};
    });
  }
  if (upload) {
    var upload=document.getElementById("upload-form");
    upload.addEventListener('change', function(e) {
      e.preventDefault();
      const formData = new FormData(upload);
      formData.append('folderName', folderName);
        fetch("/upload_file", {
              method: "POST",
              body: formData,
          })
        .then(response => response.json())
        .then(data => {
          alert("Save!");
          updateList(folderName);
        })
        .catch(error => {
          alert('Error:', error);
          console.error('Error:', error);
        });
    });
  }
});
