import React, { useState } from 'react';
import { ShoppingCart, X, Plus, Minus, Trash2 } from 'lucide-react';
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";

// Import all images
import comparativeStudyImg from '../../img/comparativeStudy.png';
import taiChiCirclesImg from '../../img/TaiChiChuanCircles.jpg';
import ebookImg from '../../img/ebook.gif';
import newImg from '../../img/new.png';
import smallFrame15Img from '../../img/15TechniqueSmallFrameSoloFormCover.gif';
import largeFrame12Img from '../../img/12TechniquesLargeFrameSoloFormCover.gif';
import mediumFrame8Img from '../../img/8TechniquesMediumFrameSoloFormCover.gif';
import beginnersCoverImg from '../../img/beginnersCover.jpg';
import largeFrameCoverImg from '../../img/largeFrameCover.jpg';
import centerHarmonyImg from '../../img/centerHarmonyQigong.gif';
import threeCirclesImg from '../../img/threeCirclesExercise.gif';
import returningTaiChiImg from '../../img/ReturningTaiChi.jpg';
import taiChiGongImg from '../../img/TaiChiGong.gif';
import technique11Img from '../../img/11_Technique.jpg';
import sword22Img from '../../img/22_sword.jpg';
import phcoverImg from '../../img/phcover.jpg';
import taichiFundamentalsImg from '../../img/taichifundamentals.jpg';
import baduanjinImg from '../../img/baduanjinfinalcover.jpg';
import animals1Img from '../../img/13animalsform1.jpg';
import animals2Img from '../../img/13animalsform2.jpg';
import broadsword26Img from '../../img/26taichibroadsword.jpg';
import internal8Img from '../../img/8_internal.jpg';
import techniq9Img from '../../img/9_techniq.jpg';
import panTaichiImg from '../../img/pan_taichi.jpg';

// PayPal configuration - REPLACE WITH YOUR CLIENT ID
const PAYPAL_CLIENT_ID = process.env.PAYPAL_CLIENT_ID;

export const BooksAndVideos = () => {
  const [shippingRegion, setShippingRegion] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [cart, setCart] = useState([]);

  const books = [
    {
      id: 1,
      title: "Tai Chi Chuan: A Comparative Study",
      description: `In Tai Chi Chuan: A Comparative Study, author and renowned practitioner Vincent Chu lays out in clear language and detailed photographs the theory and practice of Tai Chi Chuan. Chu's introduction and teaching clarify important concepts and points of emphasis that have until now remained elusive in the available literature on the subject. From basic demonstrations of proper posture to an eye-opening discussion of 'intent', this book offers something for practitioners of all levels. Chu presents three complete short forms for those interested in learning a Tai Chi Chuan routine suitable to their health and objectives.`,
      cost: 27.95,
      image: comparativeStudyImg,
      type: 'book',
      
    },
    {
      id: 2,
      title: "Tai Chi Chuan Circle",
      description: `The Circle is a simple symbol. It is a product of ancient Chinese knowledge and a symbol of ancient Chinese traditional culture. The circle represents the universe and everything that manifests within it. All natural phenomena and humanity's development operate in an infinite process or circle. Therefore, circles represent an idea, an operation, beauty, and protection. Physical activity such as Tai Chi Chuan is composed of health, martial arts, and performing arts values.`,
      image: taiChiCirclesImg,
      cost: 41.01,
      type: 'book',
      externalLink: "https://www.lulu.com/shop/vincent-chu/tai-chi-chuan-circle/paperback/product-kv88y9r.html?q=vincent+chu&page=1&pageSize=4"
    },
    {
      id: 3,
      title: 'Practical Use Of Tai Chi Chuan: It\'s Application and Variations',
      cost: 24.95,
      image: ebookImg,
      type: 'book',
      description: 'A comprehensive guide to practical Tai Chi applications and variations.',
    }
  ];

  const dvds = [
    { id: 4, title: 'Yang Style Tai Chi Chuan Medium Frame Solo Form', cost: 99.95, runtime: '3 hours 20 Minutes', details: 'Two DVD set', image: newImg, type: 'dvd' },
    { id: 5, title: 'Fifteen Technique Small Frame Solo Form', cost: 29.95, runtime: '58 Minutes', image: smallFrame15Img, type: 'dvd' },
    { id: 6, title: 'Twelve Techniques Large Frame Solo Form', cost: 29.95, runtime: '74 Minutes', image: largeFrame12Img, type: 'dvd' },
    { id: 7, title: 'Eight Techniques Medium Frame Solo Form', cost: 29.95, runtime: '59 Minutes', image: mediumFrame8Img, type: 'dvd' },
    { id: 8, title: 'Tai Chi Chuan for Beginners', cost: 29.95, runtime: '55 Minutes', image: beginnersCoverImg, type: 'dvd' },
    { id: 9, title: 'Yang Family Tai Chi Chuan: Large Frame Short Form', cost: 39.95, runtime: '52 Minutes', image: largeFrameCoverImg, type: 'dvd' },
    { id: 10, title: 'Center Harmony Qigong', cost: 29.95, runtime: '45 Minutes', image: centerHarmonyImg, type: 'dvd' },
    { id: 11, title: 'Three Circles Exercise', cost: 29.95, runtime: '45 Minutes', image: threeCirclesImg, type: 'dvd' },
    { id: 12, title: '12 Techniques Returning Tai Chi Chuan Solo Form', cost: 29.95, runtime: '1 hour 39 Minutes', image: returningTaiChiImg, type: 'dvd' },
    { id: 13, title: 'Tai Chi Gong', cost: 29.95, runtime: '33 Minutes 27 Seconds', image: taiChiGongImg, type: 'dvd' },
    { id: 14, title: '11 Techniques AJ Tai Chi Chuan', cost: 29.95, runtime: '37 Minutes 9 Seconds', image: technique11Img, type: 'dvd' },
    { id: 15, title: '22 Technique Tai Chi Sword Form DVD', cost: 29.95, runtime: '28 Minutes 17 Seconds', image: sword22Img, type: 'dvd', downloadLink: 'https://vimeo.com/ondemand/22taichisword' },
    { id: 16, title: 'Tai Chi Chuan Push Hands Exercises DVD', cost: 29.95, runtime: '22 Minutes 39 Seconds', image: phcoverImg, type: 'dvd' },
    { id: 17, title: 'Tai Chi Chuan Fundamentals Training DVD', cost: 29.95, runtime: '31 Minutes 17 Seconds', image: taichiFundamentalsImg, type: 'dvd' },
    { id: 18, title: 'Ba Duan Jin Qigong DVD', cost: 29.95, runtime: '40 Minutes 0 Seconds', image: baduanjinImg, type: 'dvd' },
    { id: 19, title: '13 Animals Form: 13 Ways to Solidifying the Elixir: Part One', cost: 49.95, runtime: '2 hours 9 Minutes', image: animals1Img, type: 'dvd' },
    { id: 20, title: '13 Animals Form: 13 Ways to Solidifying the Elixir: Part Two', cost: 49.95, runtime: '1 hours 45 Minutes', image: animals2Img, type: 'dvd' },
    { id: 21, title: '26 Techniques Tai Chi Broadsword', cost: 29.95, runtime: '38 Minutes 49 Seconds', image: broadsword26Img, type: 'dvd' },
    { id: 22, title: 'Internal Martial Art Eight Zhan Zhuang Techniques', cost: 49.95, runtime: '25 Minutes 24 Seconds', image: internal8Img, type: 'dvd' },
    { id: 23, title: 'Nine Techniques Large Frame Form', cost: 29.95, runtime: '47 Minutes 08 Seconds', image: techniq9Img, type: 'dvd' },
    { id: 24, title: 'Pan Gu Tai Chi Moving Form', cost: 29.95, runtime: '59 Minutes 07 Seconds', image: panTaichiImg, type: 'dvd' }
  ];

  // Calculate shipping
  const calculateShipping = () => {
    if (!shippingRegion || cart.length === 0) return 0;
    const firstItemShipping = shippingRegion === 'US' ? 11.00 : 20.00;
    const additionalItemsShipping = (cart.length - 1) * 5.00;
    return firstItemShipping + additionalItemsShipping;
  };

  // Calculate totals
  const subtotal = cart.reduce((sum, item) => sum + (item.cost * item.quantity), 0);
  const shipping = calculateShipping();
  const total = subtotal + shipping;

  const handleAddToCart = (product) => {
    if (!shippingRegion) {
      setShowModal(true);
      return false;
    }
    
    const existingItem = cart.find(item => item.id === product.id);
    if (existingItem) {
      setCart(cart.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
    return true;
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity === 0) {
      setCart(cart.filter(item => item.id !== productId));
    } else {
      setCart(cart.map(item => 
        item.id === productId 
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.id !== productId));
  };

  const handleRegionSelect = (region) => {
    setShippingRegion(region);
    setShowModal(false);
  };

  // PayPal order creation
  const createOrder = (data, actions) => {
    return actions.order.create({
      purchase_units: [{
        amount: {
          value: total.toFixed(2),
          breakdown: {
            item_total: { value: subtotal.toFixed(2), currency_code: "USD" },
            shipping: { value: shipping.toFixed(2), currency_code: "USD" }
          }
        },
        items: cart.map(item => ({
          name: item.title,
          unit_amount: { value: item.cost.toFixed(2), currency_code: "USD" },
          quantity: item.quantity.toString()
        }))
      }]
    });
  };

  // PayPal payment approval
  const onApprove = (data, actions) => {
    return actions.order.capture().then((details) => {
      alert(`Transaction completed by ${details.payer.name.given_name}!`);
      setCart([]);
      setShowCart(false);
    });
  };

  return (
    <PayPalScriptProvider options={{ "client-id": PAYPAL_CLIENT_ID, currency: "USD" }}>
      <div className="container-fluid px-4 my-5">
        {/* Header */}
        <div className="row mb-4">
          <div className="col-12">
            <div className="d-flex justify-content-between align-items-center flex-wrap gap-3 p-3 bg-white rounded shadow-sm">
              <select
                value={shippingRegion}
                onChange={(e) => handleRegionSelect(e.target.value)}
                className="form-select"
                style={{ maxWidth: '250px' }}
              >
                <option value="">Select Shipping Region</option>
                <option value="US">United States</option>
                <option value="Non US">Outside of US</option>
              </select>
              <button 
                className="btn btn-primary d-flex align-items-center gap-2"
                onClick={() => setShowCart(true)}
              >
                <ShoppingCart size={20} />
                <span>View Cart ({cart.length})</span>
              </button>
            </div>
          </div>
        </div>

        <h1 className="text-center mb-5">Books And Videos</h1>

        {/* Books Section */}
        <section className="mb-5">
          <h2 className="text-center mb-4">Books</h2>
          <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {books.map((book) => (
              <div key={book.id} className="col">
                <div className="card shadow-sm h-100">
                  <img 
                    src={book.image} 
                    className="card-img-top p-3" 
                    alt={book.title}
                    style={{ height: '250px', objectFit: 'contain' }}
                  />
                  <div className="card-body d-flex flex-column">
                    <h5 className="card-title">{book.title}</h5>
                    {book.description && (
                      <p className="card-text" style={{ textAlign: 'justify', fontSize: '0.9rem' }}>
                        {book.description.length > 150 
                          ? `${book.description.substring(0, 150)}...` 
                          : book.description}
                      </p>
                    )}
                    <p className="card-text font-weight-bold mt-auto mb-3">
                      Cost: ${book.cost.toFixed(2)}
                    </p>
                    <div className="d-flex flex-column gap-2">
                      <button 
                        onClick={() => handleAddToCart(book)} 
                        className="btn btn-warning w-100"
                      >
                        Add To Cart
                      </button>
                      {book.externalLink && (
                        <a 
                          href={book.externalLink} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="btn btn-outline-primary w-100"
                        >
                          Buy Direct
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <hr className="my-5" />

        {/* DVDs Section */}
        <section className="mb-5">
          <h2 className="text-center mb-4">DVDs</h2>
          <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {dvds.map((dvd) => (
              <div key={dvd.id} className="col">
                <div className="card shadow-sm h-100">
                  <img 
                    src={dvd.image} 
                    className="card-img-top p-3" 
                    alt={dvd.title}
                    style={{ height: '200px', objectFit: 'contain' }}
                  />
                  <div className="card-body d-flex flex-column">
                    <h6 className="card-title">{dvd.title}</h6>
                    {dvd.details && <p className="text-muted small mb-1">{dvd.details}</p>}
                    <p className="text-muted small mb-2">Running Time: {dvd.runtime}</p>
                    <p className="font-weight-bold mb-3">USD ${dvd.cost.toFixed(2)}</p>
                    <div className="d-flex flex-column gap-2 mt-auto">
                      <button 
                        onClick={() => handleAddToCart(dvd)} 
                        className="btn btn-warning w-100"
                      >
                        Add To Cart
                      </button>
                      {dvd.downloadLink && (
                        <a 
                          href={dvd.downloadLink} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="btn btn-outline-primary w-100"
                        >
                          Download
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Shipping Info */}
        <div className="alert alert-info text-center">
          <p className="mb-1"><strong>First Item Shipping and Handling within the U.S.: $11.00</strong></p>
          <p className="mb-1"><strong>First Item Shipping and Handling outside of the U.S.: $20.00</strong></p>
          <p className="mb-0"><strong>For every additional item: $5.00</strong></p>
        </div>

        {/* Region Selection Modal */}
        {showModal && (
          <div 
            className="modal show d-block" 
            style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
            onClick={() => setShowModal(false)}
          >
            <div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Select Shipping Region</h5>
                  <button 
                    type="button" 
                    className="btn-close" 
                    onClick={() => setShowModal(false)}
                  ></button>
                </div>
                <div className="modal-body">
                  <p>Please select the region where you are located:</p>
                  <select 
                    onChange={(e) => { if (e.target.value) { handleRegionSelect(e.target.value); }}} 
                    className="form-select"
                  >
                    <option value="">Select</option>
                    <option value="US">United States</option>
                    <option value="Non US">Outside of US</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Shopping Cart Modal */}
        {showCart && (
          <div 
            className="modal show d-block" 
            style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
            onClick={() => setShowCart(false)}
          >
            <div className="modal-dialog modal-dialog-centered modal-lg" onClick={(e) => e.stopPropagation()}>
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Shopping Cart</h5>
                  <button 
                    type="button" 
                    className="btn-close" 
                    onClick={() => setShowCart(false)}
                  ></button>
                </div>
                <div className="modal-body">
                  {cart.length === 0 ? (
                    <p className="text-center text-muted">Your cart is empty</p>
                  ) : (
                    <>
                      {cart.map((item) => (
                        <div key={item.id} className="d-flex align-items-center mb-3 pb-3 border-bottom">
                          <img src={item.image} alt={item.title} style={{ width: '80px', height: '80px', objectFit: 'contain' }} />
                          <div className="flex-grow-1 ms-3">
                            <h6 className="mb-1">{item.title}</h6>
                            <p className="mb-0 text-muted">${item.cost.toFixed(2)}</p>
                          </div>
                          <div className="d-flex align-items-center gap-2">
                            <button 
                              className="btn btn-sm btn-outline-secondary"
                              onClick={() => updateQuantity(item.id, item.quantity - 1)}
                            >
                              <Minus size={16} />
                            </button>
                            <span className="px-2">{item.quantity}</span>
                            <button 
                              className="btn btn-sm btn-outline-secondary"
                              onClick={() => updateQuantity(item.id, item.quantity + 1)}
                            >
                              <Plus size={16} />
                            </button>
                            <button 
                              className="btn btn-sm btn-outline-danger ms-2"
                              onClick={() => removeFromCart(item.id)}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                      
                      <div className="mt-4">
                        <div className="d-flex justify-content-between mb-2">
                          <span>Subtotal:</span>
                          <span>${subtotal.toFixed(2)}</span>
                        </div>
                        <div className="d-flex justify-content-between mb-2">
                          <span>Shipping ({shippingRegion}):</span>
                          <span>${shipping.toFixed(2)}</span>
                        </div>
                        <div className="d-flex justify-content-between fw-bold fs-5 pt-2 border-top">
                          <span>Total:</span>
                          <span>${total.toFixed(2)}</span>
                        </div>
                      </div>

                      <div className="mt-4">
                        <PayPalButtons
                          createOrder={createOrder}
                          onApprove={onApprove}
                          style={{ layout: "vertical" }}
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </PayPalScriptProvider>
  );
};

export default BooksAndVideos;