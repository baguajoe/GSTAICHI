import React from 'react';

const FormattedContent = ({ content, images, className = '' }) => {
  if (!content) return null;

  const processContent = (text) => {
    if (!text) return null;

    let currentList = [];
    let isInList = false;
    
    return text.split('\n').map((line, index) => {
      // Process headers
      if (line.startsWith('# ')) {
        return <h1 key={index} className="text-center mb-4">{line.substring(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={index} className="mb-3">{line.substring(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={index} className="mb-2">{line.substring(4)}</h3>;
      }

      // Process blockquotes
      if (line.startsWith('> ')) {
        return (
          <blockquote key={index} className="blockquote border-start border-3 ps-4 my-4 fst-italic">
            {processInlineFormatting(line.substring(2))}
          </blockquote>
        );
      }

      // Process lists
      if (line.startsWith('* ')) {
        if (!isInList) {
          currentList = [];
          isInList = true;
        }
        currentList.push(processInlineFormatting(line.substring(2)));
        
        // If next line isn't a list item, render the list
        if (index === text.split('\n').length - 1 || 
            !text.split('\n')[index + 1].startsWith('* ')) {
          isInList = false;
          return (
            <ul key={index} className="list-group list-group-flush my-3">
              {currentList.map((item, i) => (
                <li key={i} className="list-group-item border-0 ps-0">{item}</li>
              ))}
            </ul>
          );
        }
        return null;
      }

      // Process numbered lists
      if (line.match(/^\d+\. /)) {
        if (!isInList) {
          currentList = [];
          isInList = true;
        }
        currentList.push(processInlineFormatting(line.substring(line.indexOf('. ') + 2)));
        
        // If next line isn't a list item, render the list
        if (index === text.split('\n').length - 1 || 
            !text.split('\n')[index + 1].match(/^\d+\. /)) {
          isInList = false;
          return (
            <ol key={index} className="list-group list-group-numbered my-3">
              {currentList.map((item, i) => (
                <li key={i} className="list-group-item border-0 ps-0">{item}</li>
              ))}
            </ol>
          );
        }
        return null;
      }

      // Process images
      if (line.startsWith('![')) {
        const match = line.match(/!\[(.*?)\]\((.*?)\)/);
        if (match) {
          const alt = match[1];
          const src = match[2];
          const imageData = images?.find(img => img.url === src);
          
          return (
            <figure key={index} className="figure my-4 text-center">
              <img 
                src={src} 
                alt={alt} 
                className="figure-img img-fluid rounded shadow-sm"
              />
              {imageData?.caption && (
                <figcaption className="figure-caption text-center mt-2">
                  {imageData.caption}
                </figcaption>
              )}
            </figure>
          );
        }
      }

      // Process dividers
      if (line.startsWith('---')) {
        return <hr key={index} className="my-4" />;
      }

      // Process indentation
      if (line.startsWith('    ')) {
        return (
          <p key={index} className="mb-3 ps-4">
            {processInlineFormatting(line.trim())}
          </p>
        );
      }

      // Process inline formatting and regular paragraphs
      return line.trim() ? (
        <p key={index} className="mb-3">
          {processInlineFormatting(line)}
        </p>
      ) : <br key={index} />;
    }).filter(Boolean); // Remove null elements from lists processing
  };

  const processInlineFormatting = (text) => {
    if (!text) return '';
    
    // Process bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Process italic
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Process code
    text = text.replace(/`(.*?)`/g, '<code class="bg-light px-1 rounded">$1</code>');
    // Process links
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-decoration-none">$1</a>');
    
    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  return (
    <div className={`content-wrapper ${className}`}>
      {processContent(content)}
    </div>
  );
};

export default FormattedContent;